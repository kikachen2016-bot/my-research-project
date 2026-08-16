import base64
import logging

from openai import OpenAI

from ..config import settings
from .bars_loader import criteria_prompt_block

logger = logging.getLogger(__name__)

MAX_QUESTIONS = 5
_MAX_CONTEXT_CHARS = 3000  # per document, to keep prompt tokens reasonable

FALLBACK_QUESTIONS = [
    "まずは自己紹介をお願いします。これまでのご経歴も含めて教えてください。",
    "これまで携わったプロジェクトの中で、最も技術的に難しかった課題と、それをどう解決したか教えてください。",
    "チーム開発の中で、あなたが果たした役割や工夫した点を教えてください。",
    "日本語でのコミュニケーションにおいて、意識していることはありますか？",
    "今後挑戦したい技術や、キャリアの方向性について教えてください。",
]

FALLBACK_FEEDBACK = (
    "（フォールバック評価：OpenAI APIキーが未設定です）\n\n"
    "■ BARS評価\n"
    "①日本語の自然さ：Level 3 - 概ね自然ですが、結論を先に述べるとより明確になります。\n"
    "②日本語の自然さ（非言語）：Level 3 - 音声面接として参考評価です。\n"
    "③STAR構造（論理性）：Level 3 - 状況・行動・結果の流れをより意識すると良くなります。\n"
    "④技術説明の深さ：Level 3 - 具体的な数値や選定理由を加えると説得力が増します。\n"
    "⑤論理性（一貫性）：Level 3 - 主張と根拠の対応関係を意識してください。\n\n"
    "総合評価：Level 3/5\n\n"
    "■ 面接コーチングアドバイス\n"
    "【強みのアピール不足】履歴書の強みが十分に言語化できていない箇所が見受けられます。\n"
    "【改善例】具体的なプロジェクト成果や数値を交えて説明するとより効果的です。\n"
    "【次回の注意点】曖昧な表現を避け、STARフォーマット（状況・課題・行動・結果）を意識してください。"
)


def _context_block(job_description: str, resume_text: str) -> str:
    parts = []
    if job_description.strip():
        parts.append(f"【求人案件概要】\n{job_description.strip()[:_MAX_CONTEXT_CHARS]}")
    if resume_text.strip():
        parts.append(f"【候補者の履歴書・職務経歴書】\n{resume_text.strip()[:_MAX_CONTEXT_CHARS]}")
    return "\n\n".join(parts)


def _build_question_system_prompt(
    job_description: str,
    resume_text: str,
    question_number: int,
) -> str:
    ctx = _context_block(job_description, resume_text)
    ctx_section = f"\n\n{ctx}\n\n" if ctx else "\n\n"

    if question_number == 1:
        instruction = "1問目として、候補者に自己紹介と職歴の概要を自由に語ってもらってください。"
    else:
        instruction = (
            f"{question_number}問目です。"
            "これまでの回答・履歴書・案件要件を照らし合わせ、"
            "技術力（アーキテクチャ判断・問題解決の深さ）、"
            "プロジェクト推進力（スコープ管理・チームリード経験）、"
            "日本語コミュニケーション力のいずれかを深掘りしてください。"
            "すでに聞いた質問と重複しないようにしてください。"
        )

    return (
        "あなたはIT企業の採用面接官です。"
        "プロジェクトマネージャー、テックリード、人事担当者の視点を合わせ持ち、候補者を総合的に評価します。"
        f"{ctx_section}"
        f"{instruction}\n\n"
        "質問は1つだけ、簡潔に出してください（前置きや挨拶は不要。質問文のみを出力）。"
        f"全{MAX_QUESTIONS}問行います。"
    )


def _build_feedback_system_prompt(job_description: str = "", resume_text: str = "") -> str:
    ctx = _context_block(job_description, resume_text)
    ctx_section = f"\n\n{ctx}\n\n" if ctx else "\n\n"

    return (
        "あなたはIT企業の採用面接官兼キャリアコーチです。"
        "プロジェクトマネージャー、テックリード、人事担当者の視点を合わせ持ちます。"
        f"{ctx_section}"
        "これまでの質疑応答を踏まえて、以下の2部構成でフィードバックを行ってください。\n\n"
        f"【BARS評価基準】\n{criteria_prompt_block()}\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "■ 第1部：BARS評価\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "1. 5項目それぞれについて、1〜5のレベルと判定根拠を簡潔に述べる\n"
        "   （②日本語の自然さ（非言語）は、音声面接として発話の流暢さ・明瞭さから評価する）\n"
        "2. 案件要件との適合度コメント（案件情報がある場合）\n"
        "3. 良かった点\n"
        "4. 改善が必要な点\n"
        "5. 総合評価（5項目の平均を四捨五入した1〜5のレベル）\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "■ 第2部：面接コーチングアドバイス\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "履歴書・案件要件・実際の回答内容を照らし合わせ、候補者が次回の面接でより良いパフォーマンスを発揮できるよう、"
        "具体的なコーチングアドバイスを提供してください。\n\n"
        "6. 【強みのアピール不足】\n"
        "   履歴書や経歴から本来アピールできたはずなのに、面接の回答の中で十分に言葉にできていなかった強みや実績を"
        "   具体的に指摘してください。（例：「〇〇の経験があるのに、△△の質問でその点に触れられませんでした」）\n\n"
        "7. 【論理性・一貫性の問題点】\n"
        "   回答の中で論理が不明瞭・支離滅裂・前後矛盾していた箇所があれば、その質問と回答を具体的に参照しながら、"
        "   なぜ問題なのかを説明してください。問題がなければ「特になし」と記載してください。\n\n"
        "8. 【こう答えるとよかった（改善例）】\n"
        "   上記の問題点（強みのアピール不足・論理的問題）に対して、具体的にどう答えればより効果的だったかを"
        "   回答例として提示してください。\n\n"
        "9. 【次回に向けた注意点】\n"
        "   この面接全体を通じて、次回は避けるべき回答パターンや表現を明示してください。"
        "   （例：「〜のような曖昧な表現は避け、代わりに〜で答えましょう」）\n\n"
        "面接官・コーチとして候補者に直接語りかける形式で、日本語でまとめてください。"
    )


def _to_chat_messages(history: list[dict]) -> list[dict]:
    return [
        {"role": "assistant" if item["role"] == "interviewer" else "user", "content": item["content"]}
        for item in history
    ]


def generate_tts(text: str) -> str:
    """Return base64-encoded MP3 audio from OpenAI TTS, or empty string on failure."""
    if not settings.openai_api_key:
        return ""
    try:
        client = OpenAI(api_key=settings.openai_api_key)
        response = client.audio.speech.create(
            model="tts-1",
            voice="nova",
            input=text,
            response_format="mp3",
        )
        return base64.b64encode(response.content).decode()
    except Exception as e:
        logger.error("TTS generation failed: %s", e)
        return ""


def get_next_turn(
    history: list[dict],
    include_audio: bool = False,
    job_description: str = "",
    resume_text: str = "",
) -> dict:
    questions_asked = sum(1 for item in history if item["role"] == "interviewer")
    if questions_asked >= MAX_QUESTIONS:
        result = _generate_feedback(history, job_description, resume_text)
    else:
        result = _generate_question(history, questions_asked + 1, job_description, resume_text)
    result["audio_base64"] = generate_tts(result["content"]) if include_audio else ""
    return result


def _generate_question(
    history: list[dict],
    question_number: int,
    job_description: str = "",
    resume_text: str = "",
) -> dict:
    if not settings.openai_api_key:
        content = FALLBACK_QUESTIONS[question_number - 1]
        return {"content": content, "is_final": False, "question_number": question_number}

    try:
        client = OpenAI(api_key=settings.openai_api_key)
        system_prompt = _build_question_system_prompt(job_description, resume_text, question_number)
        messages = [
            {"role": "system", "content": system_prompt},
            *_to_chat_messages(history),
        ]
        response = client.chat.completions.create(
            model=settings.openai_model,
            temperature=0.6,
            messages=messages,
        )
        content = (response.choices[0].message.content or "").strip() or FALLBACK_QUESTIONS[question_number - 1]
        return {"content": content, "is_final": False, "question_number": question_number}
    except Exception as e:
        logger.error("OpenAI call failed, using fallback question: %s", e)
        content = FALLBACK_QUESTIONS[question_number - 1]
        return {"content": content, "is_final": False, "question_number": question_number}


def _generate_feedback(
    history: list[dict],
    job_description: str = "",
    resume_text: str = "",
) -> dict:
    if not settings.openai_api_key:
        return {"content": FALLBACK_FEEDBACK, "is_final": True, "question_number": MAX_QUESTIONS}

    try:
        client = OpenAI(api_key=settings.openai_api_key)
        messages = [
            {"role": "system", "content": _build_feedback_system_prompt(job_description, resume_text)},
            *_to_chat_messages(history),
            {"role": "user", "content": "以上で面接は終了です。総合的なフィードバックをお願いします。"},
        ]
        response = client.chat.completions.create(
            model=settings.openai_model,
            temperature=0.4,
            messages=messages,
        )
        content = (response.choices[0].message.content or "").strip() or FALLBACK_FEEDBACK
        return {"content": content, "is_final": True, "question_number": MAX_QUESTIONS}
    except Exception as e:
        logger.error("OpenAI call failed, using fallback feedback: %s", e)
        return {"content": FALLBACK_FEEDBACK, "is_final": True, "question_number": MAX_QUESTIONS}
