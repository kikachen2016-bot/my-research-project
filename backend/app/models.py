from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from .database import Base


# --- 面談前準備支援システム ---

class CandidateProfile(Base):
    __tablename__ = "candidate_profiles"

    id               = Column(Integer, primary_key=True, index=True)
    name             = Column(String(100), nullable=False)
    years_experience = Column(Integer, nullable=False)
    skills           = Column(Text, nullable=False)
    japanese_level   = Column(String(20), nullable=False)
    work_summary     = Column(Text, nullable=False)
    notes            = Column(Text, nullable=True)
    created_at       = Column(DateTime, default=datetime.utcnow, nullable=False)

    preparations = relationship("InterviewPreparation", back_populates="candidate_profile", cascade="all, delete-orphan")


class JobPosting(Base):
    __tablename__ = "job_postings"

    id                     = Column(Integer, primary_key=True, index=True)
    title                  = Column(String(200), nullable=False)
    required_skills        = Column(Text, nullable=False)
    description            = Column(Text, nullable=True)
    interview_duration_min = Column(Integer, nullable=False)
    interview_purpose      = Column(Text, nullable=False)
    created_at             = Column(DateTime, default=datetime.utcnow, nullable=False)

    preparations = relationship("InterviewPreparation", back_populates="job_posting", cascade="all, delete-orphan")


class InterviewPreparation(Base):
    __tablename__ = "interview_preparations"

    id                   = Column(Integer, primary_key=True, index=True)
    candidate_profile_id = Column(Integer, ForeignKey("candidate_profiles.id"), nullable=False)
    job_posting_id       = Column(Integer, ForeignKey("job_postings.id"), nullable=False)
    extra_notes          = Column(Text, nullable=True)

    one_minute_intro      = Column(Text, nullable=True)
    three_minute_intro    = Column(Text, nullable=True)
    matching_points_json  = Column(Text, nullable=True)
    risk_points_json      = Column(Text, nullable=True)
    expected_questions_json = Column(Text, nullable=True)
    reverse_questions_json  = Column(Text, nullable=True)
    preparation_advice_json = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    candidate_profile = relationship("CandidateProfile", back_populates="preparations")
    job_posting       = relationship("JobPosting", back_populates="preparations")


class Interview(Base):
    __tablename__ = "interviews"

    id = Column(Integer, primary_key=True, index=True)
    candidate_name = Column(String(100), nullable=False)
    question = Column(Text, nullable=False)
    transcript = Column(Text, nullable=False)
    overall_level = Column(Integer, nullable=False)
    summary_comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    evaluation = relationship("Evaluation", back_populates="interview", uselist=False, cascade="all, delete-orphan")


class Evaluation(Base):
    __tablename__ = "evaluations"

    id = Column(Integer, primary_key=True, index=True)
    interview_id = Column(Integer, ForeignKey("interviews.id"), nullable=False, unique=True)

    japanese_natural = Column(Integer, nullable=False)
    nonverbal_natural = Column(Integer, nullable=False)
    star_logic = Column(Integer, nullable=False)
    technical_depth = Column(Integer, nullable=False)
    logic_consistency = Column(Integer, nullable=False)

    advice_1 = Column(String(255), nullable=True)
    advice_2 = Column(String(255), nullable=True)
    advice_3 = Column(String(255), nullable=True)

    criterion_feedbacks_json = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    interview = relationship("Interview", back_populates="evaluation")


# --- 面談全体評価モデル ---

class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id = Column(Integer, primary_key=True, index=True)
    candidate_name = Column(String(100), nullable=False)
    overall_score = Column(Float, nullable=False)
    pass_decision = Column(String(50), nullable=False)
    fatal_flaw_triggered = Column(Boolean, default=False, nullable=False)
    fatal_flaw_reason = Column(Text, nullable=True)
    summary_comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    turns = relationship(
        "Turn",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="Turn.turn_index",
    )
    phase_scores = relationship("PhaseScore", back_populates="session", cascade="all, delete-orphan")


class Turn(Base):
    __tablename__ = "turns"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("interview_sessions.id"), nullable=False)
    turn_index = Column(Integer, nullable=False)
    phase = Column(String(30), nullable=False)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    jp_clarity = Column(Float, nullable=False)
    logical = Column(Float, nullable=False)
    technical = Column(Float, nullable=False)
    phase_score = Column(Float, nullable=False)
    feedback = Column(Text, nullable=True)

    session = relationship("InterviewSession", back_populates="turns")


class PhaseScore(Base):
    __tablename__ = "phase_scores"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("interview_sessions.id"), nullable=False)
    phase = Column(String(30), nullable=False)
    score = Column(Float, nullable=False)
    feedback = Column(Text, nullable=True)

    session = relationship("InterviewSession", back_populates="phase_scores")
