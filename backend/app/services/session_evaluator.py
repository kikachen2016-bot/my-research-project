import json
import logging
from statistics import mean

from openai import OpenAI

logger = logging.getLogger(__name__)

from ..config import settings
from ..schemas import TurnInput

PHASE_LABELS = {
    "self_intro": "自己紹介",
    "technical_qa": "技術質疑",
    "condition_check": "条件確認",
    "reverse_question": "逆質問",
    "other": "その他",
}

SYSTEM_PROMPT = """
あなたはITエンジニア面談の評価者です。
面談の複数ターンをBARS観点で厳密に評価してください。
出力は必ずJSONのみで返してください。
""".strip()


def _clamp(value, lo: float = 1.0, hi: float = 5.0) -> float:
    try:
        value = float(value)
    except (TypeError, ValueError):
        value = 3.0
    return max(lo, min(hi, value))


def compute_turn_phase_score(phase: str, jp_clarity: float, logical: float, technical: float) -> float:
    """フェーズごとの重み付けスコアを計算する"""
    if phase == "self_intro":
        return jp_clarity * 0.5 + logical * 0.5
    elif phase == "technical_qa":
        return technical * 0.5 + logical * 0.3 + jp_clarity * 0.2
    elif phase == "condition_check":
        return jp_clarity * 0.7 + logical * 0.3
    elif phase == "reverse_question":
        return logical * 0.5 + jp_clarity * 0.5
    else:
        return jp_clarity * 0.5 + logical * 0.5


def aggregate_phase_scores(turns_data: list[dict]) -> dict[str, float]:
    """同フェーズのターンスコアを平均してフェーズスコアを算出する"""
    phase_groups: dict[str, list[float]] = {}
    for t in turns_data:
        phase_groups.setdefault(t["phase"], []).append(t["phase_score"])
    return {phase: mean(scores) for phase, scores in phase_groups.items()}


def compute_overall_score(phase_scores: dict[str, float]) -> float:
    """
    overall_score = technical_qa×0.5 + self_intro×0.2 + condition_check×0.15 + reverse_question×0.15
    存在しないフェーズは除外して重みを正規化する
    """
    weights = {
        "technical_qa": 0.5,
        "self_intro": 0.2,
        "condition_check": 0.15,
        "reverse_question": 0.15,
    }
    present = {p: w for p, w in weights.items() if p in phase_scores}
    total_weight = sum(present.values())
    if total_weight == 0:
        return 3.0
    score = sum(phase_scores[p] * w for p, w in present.items())
    return round(score / total_weight, 2)


def check_fatal_flaws(
    turns_data: list[dict], phase_scores: dict[str, float]
) -> tuple[bool, list[str], str | None]:
    """
    致命傷ルール判定:
    - technical_qa フェーズスコア < 3 → 合格可能性：低
    - jp_clarity < 2 が複数ターン → 合格不可
    - reverse_question フェーズスコア ≤ 1.5 → 印象大幅減点
    """
    flaws: list[str] = []

    low_jp_count = sum(1 for t in turns_data if t["jp_clarity"] < 2)
    if low_jp_count >= 2:
        flaws.append("jp_clarity_critical")

    if "technical_qa" in phase_scores and phase_scores["technical_qa"] < 3:
        flaws.append("technical_qa_low")

    if "reverse_question" in phase_scores and phase_scores["reverse_question"] <= 1.5:
        flaws.append("reverse_question_critical")

    if not flaws:
        return False, [], None

    reason_map = {
        "jp_clarity_critical": "日本語の明瞭さが複数ターンにわたって著しく低い（スコア2未満）",
        "technical_qa_low": "技術質疑フェーズのスコアが3未満（現場投入可否に懸念）",
        "reverse_question_critical": "逆質問フェーズのスコアが著しく低い（理解度・主体性に問題）",
    }
    reason = "、".join(reason_map[f] for f in flaws)
    return True, flaws, reason


def determine_pass_decision(overall_score: float, flaws: list[str]) -> str:
    if "jp_clarity_critical" in flaws:
        return "合格不可"
    if "technical_qa_low" in flaws or "reverse_question_critical" in flaws:
        return "合格可能性：低"
    if overall_score >= 3.5:
        return "合格可能性：高"
    elif overall_score >= 2.5:
        return "合格可能性：中"
    else:
        return "合格可能性：低"


def build_session_prompt(candidate_name: str, turns: list[TurnInput]) -> str:
    turns_text_parts = []
    for i, t in enumerate(turns):
        phase_label = PHASE_LABELS.get(t.phase, t.phase)
        turns_text_parts.append(
            f"[ターン {i + 1}] フェーズ: {phase_label}\n質問: {t.question}\n回答: {t.answer}"
        )
    turns_text = "\n\n".join(turns_text_parts)

    turns_template = json.dumps(
        [
            {"turn_index": i, "jp_clarity": 1, "logical": 1, "technical": 1, "feedback": ""}
            for i in range(len(turns))
        ],
        ensure_ascii=False,
        indent=2,
    )

    return f"""候補者「{candidate_name}」の面談記録を評価してください。

【面談ターン一覧】
{turns_text}

【評価指示】
各ターンについて以下の3軸で1〜5の整数スコアを付けてください：
- jp_clarity: 日本語の明瞭さ（1=全く伝わらない、5=非常に明確で自然）
- logical: 論理性・構造（1=話が脱線・矛盾あり、5=STAR形式で完結・一貫性高い）
- technical: 技術の深さ（1=技術知識なし、5=技術選定理由・実績まで明確に説明）
- feedback: そのターンへの具体的な改善コメント（60文字以内）

また以下も記述してください：
- phase_feedbacks: 各フェーズへの評価コメント（40文字以内）
- summary_comment: 面談全体の総評（150文字以内、合否判断の根拠を含む）

【出力形式（JSONのみ）】
{{
  "turns": {turns_template},
  "phase_feedbacks": {{
    "self_intro": "",
    "technical_qa": "",
    "condition_check": "",
    "reverse_question": ""
  }},
  "summary_comment": ""
}}"""


def _process_gpt_response(data: dict, turns: list[TurnInput]) -> dict:
    turns_data = []
    for i, t in enumerate(turns):
        gpt_turn = next(
            (x for x in data.get("turns", []) if x.get("turn_index") == i), {}
        )
        jp_clarity = _clamp(gpt_turn.get("jp_clarity", 3))
        logical = _clamp(gpt_turn.get("logical", 3))
        technical = _clamp(gpt_turn.get("technical", 3))
        phase_score = compute_turn_phase_score(t.phase, jp_clarity, logical, technical)
        turns_data.append({
            "turn_index": i,
            "phase": t.phase,
            "question": t.question,
            "answer": t.answer,
            "jp_clarity": jp_clarity,
            "logical": logical,
            "technical": technical,
            "phase_score": round(phase_score, 2),
            "feedback": str(gpt_turn.get("feedback", "")),
        })

    phase_feedbacks: dict = data.get("phase_feedbacks", {})
    phase_scores = aggregate_phase_scores(turns_data)
    overall_score = compute_overall_score(phase_scores)
    fatal_triggered, flaws, fatal_reason = check_fatal_flaws(turns_data, phase_scores)
    pass_decision = determine_pass_decision(overall_score, flaws)
    summary_comment = str(data.get("summary_comment", ""))

    return {
        "turns_data": turns_data,
        "phase_scores": phase_scores,
        "phase_feedbacks": phase_feedbacks,
        "overall_score": overall_score,
        "pass_decision": pass_decision,
        "fatal_flaw_triggered": fatal_triggered,
        "fatal_flaw_reason": fatal_reason,
        "summary_comment": summary_comment,
    }


def _fallback_evaluate_session(candidate_name: str, turns: list[TurnInput]) -> dict:
    turns_data = []
    for i, t in enumerate(turns):
        text = t.answer.strip()
        has_tech = any(
            k.lower() in text.lower()
            for k in ["java", "python", "sql", "api", "aws", "docker", "spring", "react"]
        )
        has_result = any(k in text for k in ["結果", "改善", "%", "短縮", "向上", "件"])
        has_structure = any(k in text for k in ["なぜ", "理由", "ため", "結論", "まず"])

        jp_clarity = 3.0 if len(text) > 80 else 2.0
        logical = 3.0 if has_structure and has_result else 2.0
        technical = 3.0 if has_tech else 2.0

        phase_score = compute_turn_phase_score(t.phase, jp_clarity, logical, technical)
        turns_data.append({
            "turn_index": i,
            "phase": t.phase,
            "question": t.question,
            "answer": t.answer,
            "jp_clarity": jp_clarity,
            "logical": logical,
            "technical": technical,
            "phase_score": round(phase_score, 2),
            "feedback": "（フォールバック評価：OpenAI APIキーが未設定です）",
        })

    phase_scores = aggregate_phase_scores(turns_data)
    overall_score = compute_overall_score(phase_scores)
    fatal_triggered, flaws, fatal_reason = check_fatal_flaws(turns_data, phase_scores)
    pass_decision = determine_pass_decision(overall_score, flaws)

    return {
        "turns_data": turns_data,
        "phase_scores": phase_scores,
        "phase_feedbacks": {
            "self_intro": "自己紹介の明確さを評価しました。",
            "technical_qa": "技術的な経験について評価しました。",
            "condition_check": "稼働条件の確認内容を評価しました。",
            "reverse_question": "逆質問の内容を評価しました。",
        },
        "overall_score": overall_score,
        "pass_decision": pass_decision,
        "fatal_flaw_triggered": fatal_triggered,
        "fatal_flaw_reason": fatal_reason,
        "summary_comment": "APIキーが未設定のため、ルールベースの評価を行いました。",
    }


def evaluate_session(candidate_name: str, turns: list[TurnInput]) -> dict:
    if not settings.openai_api_key:
        return _fallback_evaluate_session(candidate_name, turns)

    try:
        client = OpenAI(api_key=settings.openai_api_key)
        response = client.chat.completions.create(
            model=settings.openai_model,
            temperature=0.2,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": build_session_prompt(candidate_name, turns)},
            ],
        )
        content = response.choices[0].message.content or "{}"
        data = json.loads(content)
        return _process_gpt_response(data, turns)
    except Exception as e:
        logger.error("OpenAI call failed, using fallback: %s", e)
        return _fallback_evaluate_session(candidate_name, turns)
