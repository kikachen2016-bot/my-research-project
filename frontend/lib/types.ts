export type CriterionLevel = {
  level: number;
  description: string;
};

export type BarsCriterion = {
  key: string;
  label: string;
  levels: CriterionLevel[];
};

export type CriterionFeedback = {
  key: string;
  score: number;
  current_issue: string;
  feedback_comment: string;
  next_action: string;
  improved_example: string;
};

export type EvaluationResult = {
  japanese_natural: number;
  nonverbal_natural: number;
  star_logic: number;
  technical_depth: number;
  logic_consistency: number;
  overall_level: number;
  summary_comment?: string | null;
  advice: string[];
  criterion_feedbacks: CriterionFeedback[];
};

export type InterviewSummary = {
  id: number;
  candidate_name: string;
  question: string;
  overall_level: number;
  created_at: string;
};

export type InterviewDetail = {
  id: number;
  candidate_name: string;
  question: string;
  transcript: string;
  overall_level: number;
  summary_comment?: string | null;
  created_at: string;
  evaluation: EvaluationResult;
};

// --- 面談全体評価 ---

export type TurnInput = {
  phase: string;
  question: string;
  answer: string;
};

export type TurnResult = {
  turn_index: number;
  phase: string;
  question: string;
  answer: string;
  jp_clarity: number;
  logical: number;
  technical: number;
  phase_score: number;
  feedback: string | null;
};

export type PhaseScoreResult = {
  phase: string;
  score: number;
  feedback: string | null;
};

export type SessionSummary = {
  id: number;
  candidate_name: string;
  overall_score: number;
  pass_decision: string;
  created_at: string;
};

export type SessionDetail = {
  id: number;
  candidate_name: string;
  overall_score: number;
  pass_decision: string;
  fatal_flaw_triggered: boolean;
  fatal_flaw_reason: string | null;
  summary_comment: string | null;
  created_at: string;
  turns: TurnResult[];
  phase_scores: PhaseScoreResult[];
};

// --- 面談前準備支援システム ---

export type ExpectedQuestion = {
  question: string;
  intent: string;
  answer_points: string[];
  caution: string;
};

export type ReverseQuestion = {
  question: string;
  purpose: string;
};

export type InterviewPreparationResult = {
  one_minute_intro: string;
  three_minute_intro: string;
  matching_points: string[];
  risk_points: string[];
  expected_questions: ExpectedQuestion[];
  reverse_questions: ReverseQuestion[];
  preparation_advice: string;
};

export type InterviewPreparationResponse = {
  id: number;
  candidate_id: number;
  job_id: number;
  result_json: InterviewPreparationResult;
};
