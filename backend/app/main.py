import json
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .config import settings
from .database import Base, engine, get_db
from .models import Evaluation, Interview, InterviewSession, Turn, PhaseScore, CandidateProfile, JobPosting, InterviewPreparation
from .schemas import (
    BarsCriterion,
    EvaluateRequest,
    EvaluationResult,
    InterviewDetail,
    InterviewSummary,
    SessionEvaluateRequest,
    SessionDetail,
    SessionSummary,
    TurnResult,
    PhaseScoreResult,
    CandidateProfileCreate,
    JobPostingCreate,
    InterviewPreparationCreate,
    InterviewPreparationResponse,
    InterviewPreparationResult,
    AiInterviewTurnRequest,
    AiInterviewTurnResponse,
)
from .services.bars_loader import load_bars_criteria
from .services.evaluator import evaluate_interview, generate_interview_preparation
from .services.file_parser import extract_text_from_resume_file
from .services.session_evaluator import evaluate_session
from .services.transcriber import transcribe_audio
from .services.ai_interview import get_next_turn


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def serialize_criterion_feedbacks(feedbacks) -> str:
    return json.dumps(
        [
            item.model_dump() if hasattr(item, "model_dump") else item.dict()
            for item in feedbacks
        ],
        ensure_ascii=False,
    )


def _session_to_detail(session: InterviewSession) -> SessionDetail:
    return SessionDetail(
        id=session.id,
        candidate_name=session.candidate_name,
        overall_score=session.overall_score,
        pass_decision=session.pass_decision,
        fatal_flaw_triggered=session.fatal_flaw_triggered,
        fatal_flaw_reason=session.fatal_flaw_reason,
        summary_comment=session.summary_comment,
        created_at=session.created_at,
        turns=[
            TurnResult(
                turn_index=t.turn_index,
                phase=t.phase,
                question=t.question,
                answer=t.answer,
                jp_clarity=t.jp_clarity,
                logical=t.logical,
                technical=t.technical,
                phase_score=t.phase_score,
                feedback=t.feedback,
            )
            for t in session.turns
        ],
        phase_scores=[
            PhaseScoreResult(
                phase=ps.phase,
                score=ps.score,
                feedback=ps.feedback,
            )
            for ps in session.phase_scores
        ],
    )


# --- ヘルスチェック ---

@app.get("/health")
def health_check():
    return {"status": "ok"}


# --- BARS評価基準 ---

@app.get(f"{settings.api_v1_prefix}/bars/criteria", response_model=list[BarsCriterion])
def get_bars_criteria():
    return load_bars_criteria()


# --- 既存：単一回答評価 ---

@app.get(f"{settings.api_v1_prefix}/interviews", response_model=list[InterviewSummary])
def list_interviews(db: Session = Depends(get_db)):
    items = db.query(Interview).order_by(Interview.created_at.desc()).all()
    return items


@app.post(f"{settings.api_v1_prefix}/interviews/evaluate", response_model=InterviewDetail)
def create_evaluation(payload: EvaluateRequest, db: Session = Depends(get_db)):
    result: EvaluationResult = evaluate_interview(payload.question, payload.transcript)

    interview = Interview(
        candidate_name=payload.candidate_name,
        question=payload.question,
        transcript=payload.transcript,
        overall_level=result.overall_level,
        summary_comment=result.summary_comment,
    )
    db.add(interview)
    db.flush()

    evaluation = Evaluation(
        interview_id=interview.id,
        japanese_natural=result.japanese_natural,
        nonverbal_natural=result.nonverbal_natural,
        star_logic=result.star_logic,
        technical_depth=result.technical_depth,
        logic_consistency=result.logic_consistency,
        advice_1=result.advice[0] if len(result.advice) > 0 else None,
        advice_2=result.advice[1] if len(result.advice) > 1 else None,
        advice_3=result.advice[2] if len(result.advice) > 2 else None,
        criterion_feedbacks_json=serialize_criterion_feedbacks(result.criterion_feedbacks),
    )

    db.add(evaluation)
    db.commit()
    db.refresh(interview)
    db.refresh(evaluation)

    return InterviewDetail(
        id=interview.id,
        candidate_name=interview.candidate_name,
        question=interview.question,
        transcript=interview.transcript,
        overall_level=interview.overall_level,
        summary_comment=interview.summary_comment,
        created_at=interview.created_at,
        evaluation=EvaluationResult(
            japanese_natural=evaluation.japanese_natural,
            nonverbal_natural=evaluation.nonverbal_natural,
            star_logic=evaluation.star_logic,
            technical_depth=evaluation.technical_depth,
            logic_consistency=evaluation.logic_consistency,
            overall_level=interview.overall_level,
            summary_comment=interview.summary_comment,
            advice=[
                item
                for item in [evaluation.advice_1, evaluation.advice_2, evaluation.advice_3]
                if item
            ],
            criterion_feedbacks=json.loads(evaluation.criterion_feedbacks_json or "[]"),
        ),
    )


# --- 新規：音声ファイルから評価 ---

@app.post(f"{settings.api_v1_prefix}/interviews/evaluate/audio", response_model=InterviewDetail)
def create_audio_evaluation(
    candidate_name: str = Form(...),
    question: str = Form(...),
    audio_file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    音声ファイルを受け取り、Whisperで文字起こししてBARS診断を行います。
    """
    content = audio_file.file.read()

    # 文字起こし
    try:
        transcript_text = transcribe_audio(content, audio_file.filename or "audio.wav")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"音声解析中にエラーが発生しました: {str(e)}")

    # 既存の評価ロジックを流用
    result: EvaluationResult = evaluate_interview(question, transcript_text)

    # DB保存
    interview = Interview(
        candidate_name=candidate_name,
        question=question,
        transcript=transcript_text,
        overall_level=result.overall_level,
        summary_comment=result.summary_comment,
    )
    db.add(interview)
    db.flush()

    evaluation = Evaluation(
        interview_id=interview.id,
        japanese_natural=result.japanese_natural,
        nonverbal_natural=result.nonverbal_natural,
        star_logic=result.star_logic,
        technical_depth=result.technical_depth,
        logic_consistency=result.logic_consistency,
        advice_1=result.advice[0] if len(result.advice) > 0 else None,
        advice_2=result.advice[1] if len(result.advice) > 1 else None,
        advice_3=result.advice[2] if len(result.advice) > 2 else None,
        criterion_feedbacks_json=serialize_criterion_feedbacks(result.criterion_feedbacks),
    )

    db.add(evaluation)
    db.commit()
    db.refresh(interview)
    db.refresh(evaluation)

    return InterviewDetail(
        id=interview.id,
        candidate_name=interview.candidate_name,
        question=interview.question,
        transcript=interview.transcript,
        overall_level=interview.overall_level,
        summary_comment=interview.summary_comment,
        created_at=interview.created_at,
        evaluation=EvaluationResult(
            japanese_natural=evaluation.japanese_natural,
            nonverbal_natural=evaluation.nonverbal_natural,
            star_logic=evaluation.star_logic,
            technical_depth=evaluation.technical_depth,
            logic_consistency=evaluation.logic_consistency,
            overall_level=interview.overall_level,
            summary_comment=interview.summary_comment,
            advice=[
                item
                for item in [evaluation.advice_1, evaluation.advice_2, evaluation.advice_3]
                if item
            ],
            criterion_feedbacks=json.loads(evaluation.criterion_feedbacks_json or "[]"),
        ),
    )


@app.get(f"{settings.api_v1_prefix}/interviews/{{interview_id}}", response_model=InterviewDetail)
def get_interview(interview_id: int, db: Session = Depends(get_db)):
    interview = db.query(Interview).filter(Interview.id == interview_id).first()
    if not interview or not interview.evaluation:
        raise HTTPException(status_code=404, detail="Interview not found")

    evaluation = interview.evaluation

    return InterviewDetail(
        id=interview.id,
        candidate_name=interview.candidate_name,
        question=interview.question,
        transcript=interview.transcript,
        overall_level=interview.overall_level,
        summary_comment=interview.summary_comment,
        created_at=interview.created_at,
        evaluation=EvaluationResult(
            japanese_natural=evaluation.japanese_natural,
            nonverbal_natural=evaluation.nonverbal_natural,
            star_logic=evaluation.star_logic,
            technical_depth=evaluation.technical_depth,
            logic_consistency=evaluation.logic_consistency,
            overall_level=interview.overall_level,
            summary_comment=interview.summary_comment,
            advice=[
                item
                for item in [evaluation.advice_1, evaluation.advice_2, evaluation.advice_3]
                if item
            ],
            criterion_feedbacks=json.loads(evaluation.criterion_feedbacks_json or "[]"),
        ),
    )


# --- 新規：面談全体評価 ---

@app.get(f"{settings.api_v1_prefix}/sessions", response_model=list[SessionSummary])
def list_sessions(db: Session = Depends(get_db)):
    items = db.query(InterviewSession).order_by(InterviewSession.created_at.desc()).all()
    return items


@app.post(f"{settings.api_v1_prefix}/sessions/evaluate", response_model=SessionDetail)
def create_session(payload: SessionEvaluateRequest, db: Session = Depends(get_db)):
    result = evaluate_session(payload.candidate_name, payload.turns)

    session = InterviewSession(
        candidate_name=payload.candidate_name,
        overall_score=result["overall_score"],
        pass_decision=result["pass_decision"],
        fatal_flaw_triggered=result["fatal_flaw_triggered"],
        fatal_flaw_reason=result["fatal_flaw_reason"],
        summary_comment=result["summary_comment"],
    )
    db.add(session)
    db.flush()

    for t in result["turns_data"]:
        db.add(Turn(
            session_id=session.id,
            turn_index=t["turn_index"],
            phase=t["phase"],
            question=t["question"],
            answer=t["answer"],
            jp_clarity=t["jp_clarity"],
            logical=t["logical"],
            technical=t["technical"],
            phase_score=t["phase_score"],
            feedback=t["feedback"],
        ))

    phase_feedbacks: dict = result.get("phase_feedbacks", {})
    for phase, score in result["phase_scores"].items():
        db.add(PhaseScore(
            session_id=session.id,
            phase=phase,
            score=score,
            feedback=phase_feedbacks.get(phase),
        ))

    db.commit()
    db.refresh(session)

    return _session_to_detail(session)


@app.get(f"{settings.api_v1_prefix}/sessions/{{session_id}}", response_model=SessionDetail)
def get_session(session_id: int, db: Session = Depends(get_db)):
    session = db.query(InterviewSession).filter(InterviewSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return _session_to_detail(session)


# --- 面談前準備支援システム ---

@app.post(f"{settings.api_v1_prefix}/candidate/upload", status_code=201)
async def upload_candidate(file: UploadFile = File(...), db: Session = Depends(get_db)):
    content = await file.read()
    try:
        resume_text = extract_text_from_resume_file(file.filename or "", content)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ファイル処理中にエラーが発生しました: {str(e)}")

    candidate = CandidateProfile(
        name="",
        years_experience=0,
        skills="",
        japanese_level="",
        work_summary=resume_text,
    )
    db.add(candidate)
    db.commit()
    db.refresh(candidate)
    return {"id": candidate.id}


@app.post(f"{settings.api_v1_prefix}/candidate", status_code=201)
def create_candidate(payload: CandidateProfileCreate, db: Session = Depends(get_db)):
    candidate = CandidateProfile(
        name="",
        years_experience=0,
        skills="",
        japanese_level="",
        work_summary=payload.resume_text,
    )
    db.add(candidate)
    db.commit()
    db.refresh(candidate)
    return {"id": candidate.id}


@app.post(f"{settings.api_v1_prefix}/job", status_code=201)
def create_job(payload: JobPostingCreate, db: Session = Depends(get_db)):
    job = JobPosting(
        title="",
        required_skills="",
        interview_duration_min=45,
        interview_purpose="[]",
        description=payload.job_description,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return {"id": job.id}


@app.post(f"{settings.api_v1_prefix}/interview-preparation", response_model=InterviewPreparationResponse)
def create_interview_preparation(payload: InterviewPreparationCreate, db: Session = Depends(get_db)):
    candidate = db.query(CandidateProfile).filter(CandidateProfile.id == payload.candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    job = db.query(JobPosting).filter(JobPosting.id == payload.job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    result = generate_interview_preparation(
        resume_text=candidate.work_summary,
        job_description=job.description or "",
    )

    preparation = InterviewPreparation(
        candidate_profile_id=candidate.id,
        job_posting_id=job.id,
        one_minute_intro=result.get("one_minute_intro", ""),
        three_minute_intro=result.get("three_minute_intro", ""),
        matching_points_json=json.dumps(result.get("matching_points", []), ensure_ascii=False),
        risk_points_json=json.dumps(result.get("risk_points", []), ensure_ascii=False),
        expected_questions_json=json.dumps(result.get("expected_questions", []), ensure_ascii=False),
        reverse_questions_json=json.dumps(result.get("reverse_questions", []), ensure_ascii=False),
        preparation_advice_json=result.get("preparation_advice", ""),
    )
    db.add(preparation)
    db.commit()
    db.refresh(preparation)

    return InterviewPreparationResponse(
        id=preparation.id,
        candidate_id=candidate.id,
        job_id=job.id,
        result_json=InterviewPreparationResult(
            one_minute_intro=preparation.one_minute_intro or "",
            three_minute_intro=preparation.three_minute_intro or "",
            matching_points=json.loads(preparation.matching_points_json or "[]"),
            risk_points=json.loads(preparation.risk_points_json or "[]"),
            expected_questions=json.loads(preparation.expected_questions_json or "[]"),
            reverse_questions=json.loads(preparation.reverse_questions_json or "[]"),
            preparation_advice=preparation.preparation_advice_json or "",
        ),
    )


def _preparation_to_response(preparation: InterviewPreparation) -> InterviewPreparationResponse:
    return InterviewPreparationResponse(
        id=preparation.id,
        candidate_id=preparation.candidate_profile_id,
        job_id=preparation.job_posting_id,
        result_json=InterviewPreparationResult(
            one_minute_intro=preparation.one_minute_intro or "",
            three_minute_intro=preparation.three_minute_intro or "",
            matching_points=json.loads(preparation.matching_points_json or "[]"),
            risk_points=json.loads(preparation.risk_points_json or "[]"),
            expected_questions=json.loads(preparation.expected_questions_json or "[]"),
            reverse_questions=json.loads(preparation.reverse_questions_json or "[]"),
            preparation_advice=preparation.preparation_advice_json or "",
        ),
    )


@app.get(f"{settings.api_v1_prefix}/interview-preparation/{{preparation_id}}", response_model=InterviewPreparationResponse)
def get_interview_preparation(preparation_id: int, db: Session = Depends(get_db)):
    preparation = db.query(InterviewPreparation).filter(InterviewPreparation.id == preparation_id).first()
    if not preparation:
        raise HTTPException(status_code=404, detail="Preparation not found")
    return _preparation_to_response(preparation)


# --- AI面接（テスト版、DB保存なし） ---

@app.post(f"{settings.api_v1_prefix}/ai-interview-voice/parse-context")
async def parse_voice_context(
    job_file: UploadFile = File(...),
    resume_file: UploadFile = File(...),
):
    try:
        job_content = await job_file.read()
        job_description = extract_text_from_resume_file(job_file.filename or "job.txt", job_content)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"案件ファイルの解析エラー: {e}")

    try:
        resume_content = await resume_file.read()
        resume_text = extract_text_from_resume_file(resume_file.filename or "resume.txt", resume_content)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"履歴書ファイルの解析エラー: {e}")

    return {"job_description": job_description, "resume_text": resume_text}


@app.post(f"{settings.api_v1_prefix}/ai-interview/turn", response_model=AiInterviewTurnResponse)
def ai_interview_turn(payload: AiInterviewTurnRequest):
    history = [item.model_dump() for item in payload.history]
    result = get_next_turn(
        history,
        include_audio=payload.include_audio,
        job_description=payload.job_description,
        resume_text=payload.resume_text,
    )
    return AiInterviewTurnResponse(
        role="interviewer",
        content=result["content"],
        is_final=result["is_final"],
        question_number=result["question_number"],
        audio_base64=result["audio_base64"],
    )
