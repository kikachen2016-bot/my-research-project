import { BarsCriterion, InterviewDetail, InterviewSummary, InterviewPreparationResponse, SessionDetail, SessionSummary, TurnInput, AiInterviewMessage, AiInterviewTurnResponse } from './types';
import { getApiBase } from './api-base';

const API_URL = getApiBase();

async function parseJson<T>(res: Response, errorMessage: string): Promise<T> {
  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(text || errorMessage);
  }
  return res.json();
}

export async function getCriteria(): Promise<BarsCriterion[]> {
  const res = await fetch(`${API_URL}/bars/criteria`, { cache: 'no-store' });
  return parseJson<BarsCriterion[]>(res, 'Failed to load BARS criteria');
}

export async function getInterviews(): Promise<InterviewSummary[]> {
  const res = await fetch(`${API_URL}/interviews`, { cache: 'no-store' });
  return parseJson<InterviewSummary[]>(res, 'Failed to load interviews');
}

export async function getInterview(id: string): Promise<InterviewDetail> {
  const res = await fetch(`${API_URL}/interviews/${id}`, { cache: 'no-store' });
  return parseJson<InterviewDetail>(res, 'Failed to load interview');
}

export async function checkHealth(): Promise<{ status: string }> {
  const baseRoot = API_URL.replace(/\/api\/v1$/, '');
  const res = await fetch(`${baseRoot}/health`, { cache: 'no-store' });
  return parseJson<{ status: string }>(res, 'Failed to check API health');
}

export async function getSessions(): Promise<SessionSummary[]> {
  const res = await fetch(`${API_URL}/sessions`, { cache: 'no-store' });
  return parseJson<SessionSummary[]>(res, 'Failed to load sessions');
}

export async function getSession(id: string): Promise<SessionDetail> {
  const res = await fetch(`${API_URL}/sessions/${id}`, { cache: 'no-store' });
  return parseJson<SessionDetail>(res, 'Failed to load session');
}

export async function getPreparation(id: string): Promise<InterviewPreparationResponse> {
  const res = await fetch(`${API_URL}/interview-preparation/${id}`, { cache: 'no-store' });
  return parseJson<InterviewPreparationResponse>(res, 'Failed to load preparation');
}

export async function postAiInterviewTurn(
  history: AiInterviewMessage[],
  includeAudio = false,
  jobDescription = '',
  resumeText = '',
): Promise<AiInterviewTurnResponse> {
  const res = await fetch(`${API_URL}/ai-interview/turn`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      history,
      include_audio: includeAudio,
      job_description: jobDescription,
      resume_text: resumeText,
    }),
    cache: 'no-store',
  });
  return parseJson<AiInterviewTurnResponse>(res, 'Failed to get next interview turn');
}

export async function parseVoiceContext(
  jobFile: File,
  resumeFile: File,
): Promise<{ job_description: string; resume_text: string }> {
  const form = new FormData();
  form.append('job_file', jobFile);
  form.append('resume_file', resumeFile);
  const res = await fetch(`${API_URL}/ai-interview-voice/parse-context`, {
    method: 'POST',
    body: form,
    cache: 'no-store',
  });
  return parseJson<{ job_description: string; resume_text: string }>(res, 'ファイルの解析に失敗しました');
}
