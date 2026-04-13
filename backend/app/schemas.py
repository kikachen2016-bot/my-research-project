from datetime import datetime
from pydantic import BaseModel, Field


# --- 既存：単一回答評価 ---

class CriterionLevel(BaseModel):
    level: int
    description: str


class BarsCriterion(BaseModel):
    key: str
    label: str
    levels: list[CriterionLevel]


class EvaluateRequest(BaseModel):
    candidate_name: str = Field(..., max_length=100)
    question: str
    transcript: str


class CriterionFeedback(BaseModel):
    key: str
    score: int
    current_issue: str
    feedback_comment: str
    next_action: str
    improved_example: str


class EvaluationResult(BaseModel):
    japanese_natural: int
    nonverbal_natural: int
    star_logic: int
    technical_depth: int
    logic_consistency: int
    overall_level: int
    summary_comment: str | None = None
    advice: list[str] = []
    criterion_feedbacks: list[CriterionFeedback] = []


class InterviewSummary(BaseModel):
    id: int
    candidate_name: str
    question: str
    overall_level: int
    created_at: datetime

    class Config:
        from_attributes = True


class InterviewDetail(BaseModel):
    id: int
    candidate_name: str
    question: str
    transcript: str
    overall_level: int
    summary_comment: str | None
    created_at: datetime
    evaluation: EvaluationResult

    class Config:
        from_attributes = True


# --- 新規：面談全体評価 ---

class TurnInput(BaseModel):
    phase: str
    question: str
    answer: str


class SessionEvaluateRequest(BaseModel):
    candidate_name: str = Field(..., max_length=100)
    turns: list[TurnInput] = Field(..., min_length=1)


class TurnResult(BaseModel):
    turn_index: int
    phase: str
    question: str
    answer: str
    jp_clarity: float
    logical: float
    technical: float
    phase_score: float
    feedback: str | None = None

    class Config:
        from_attributes = True


class PhaseScoreResult(BaseModel):
    phase: str
    score: float
    feedback: str | None = None

    class Config:
        from_attributes = True


class SessionSummary(BaseModel):
    id: int
    candidate_name: str
    overall_score: float
    pass_decision: str
    created_at: datetime

    class Config:
        from_attributes = True


class SessionDetail(BaseModel):
    id: int
    candidate_name: str
    overall_score: float
    pass_decision: str
    fatal_flaw_triggered: bool
    fatal_flaw_reason: str | None
    summary_comment: str | None
    created_at: datetime
    turns: list[TurnResult]
    phase_scores: list[PhaseScoreResult]

    class Config:
        from_attributes = True


# --- 面談前準備支援システム ---

class CandidateProfileCreate(BaseModel):
    resume_text: str


class JobPostingCreate(BaseModel):
    job_description: str


class InterviewPreparationCreate(BaseModel):
    candidate_id: int
    job_id: int


class ExpectedQuestion(BaseModel):
    question: str
    intent: str
    answer_points: list[str]
    caution: str


class ReverseQuestion(BaseModel):
    question: str
    purpose: str


class InterviewPreparationResult(BaseModel):
    one_minute_intro: str
    three_minute_intro: str
    matching_points: list[str]
    risk_points: list[str]
    expected_questions: list[ExpectedQuestion]
    reverse_questions: list[ReverseQuestion]
    preparation_advice: str


class InterviewPreparationResponse(BaseModel):
    id: int
    candidate_id: int
    job_id: int
    result_json: InterviewPreparationResult

    class Config:
        from_attributes = True
