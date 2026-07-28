import base64
import logging

from openai import OpenAI

from ..config import settings
from .bars_loader import criteria_prompt_block

logger = logging.getLogger(__name__)

MAX_QUESTIONS = 5

FALLBACK_QUESTIONS = [
    "まずは自己紹介をお願いします。これまでのご経歴も含めて教えてください。",
    "これまで携わったプロジェクトの中で、最も技術的に難しかった課題と、それをどう解決したか教えてください。",
    "チーム開発の中で、あなたが果たした役割や工夫した点を教えてください。",
    "日本語でのコミュニケーションにおいて、意識していることはありますか？",
    "今後挑戦したい技術や、キャリアの方向性について教えてください。",
]

FALLBACK_FEEDBACK = (
    "（フォールバック評価：OpenAI APIキーが未設定です）\n\n"
    "BARS評価基準に基づく簡易評価です。\n"
    "①日本語の自然さ：Level 3 - 概ね自然ですが、結論を先に述べるとより明確になります。\n"
    "②日本語の自然さ（非言語）：Level 3 - テキスト面接のため参考評価です。\n"
    "③STAR構造（論理性）：Level 3 - 状況・行動・結果の流れをより意識すると良くなります。\n"
    "④技術説明の深さ：Level 3 - 具体的な数値や選定理由を加えると説得力が増します。\n"
    "⑤論理性（一貫性）：Level 3 - 主張と根拠の対応関係を意識してください。\n\n"
    "総合評価：Level 3/5。次回は経験を裏付ける具体例をもう少し増やしてみましょう。"
)

QUESTION_SYSTEM_PROMPT = f"""
あなたはIT企業の採用面接官です。
日本語で、外国人ITエンジニアの候補者にテキストベースの模擬面接を行います。
全部で{MAX_QUESTIONS}問質問します。
質問は1つだけ、簡潔に出してください（前置きの説明や挨拶は不要、質問文のみを出力してください）。
""".strip()


def _build_feedback_system_prompt() -> str:
    return f"""
あなたはIT企業の採用面接官です。
これまでの質疑応答を踏まえて、候補者へのフィードバックを行ってください。
評価は必ず以下のBARS（行動基準評価尺度）の5項目に基づいて行ってください。

【BARS評価基準】
{criteria_prompt_block()}

【出力構成】
1. 5項目それぞれについて、1〜5のレベルと判定根拠を簡潔に述べる
   （②日本語の自然さ（非言語）は、テキスト面接のため文章の丁寧さ等から推測できる範囲で参考評価とする）
2. 良かった点
3. 改善が必要な点
4. 総合評価（5項目の平均を四捨五入した1〜5のレベル）
5. 次のステップに向けたアドバイス

面接官として候補者に直接語りかける形式で、日本語でまとめてください。
""".strip()


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


def get_next_turn(history: list[dict], include_audio: bool = False) -> dict:
    questions_asked = sum(1 for item in history if item["role"] == "interviewer")

    if questions_asked >= MAX_QUESTIONS:
        result = _generate_feedback(history)
    else:
        result = _generate_question(history, questions_asked + 1)

    result["audio_base64"] = generate_tts(result["content"]) if include_audio else ""
    return result


def _generate_question(history: list[dict], question_number: int) -> dict:
    if not settings.openai_api_key:
        content = FALLBACK_QUESTIONS[question_number - 1]
        return {"content": content, "is_final": False, "question_number": question_number}

    try:
        client = OpenAI(api_key=settings.openai_api_key)
        if question_number == 1:
            instruction = "今回は1問目です。自己紹介とこれまでの経歴を尋ねる質問にしてください。"
        else:
            instruction = (
                f"今回は{question_number}問目です。これまでの回答を踏まえ、技術力・コミュニケーション能力・"
                "経験の深さを確認する質問にしてください。これまでに聞いた質問と内容が重複しないようにしてください。"
            )

        messages = [
            {"role": "system", "content": QUESTION_SYSTEM_PROMPT + "\n" + instruction},
            *_to_chat_messages(history),
        ]
        response = client.chat.completions.create(
            model=settings.openai_model,
            temperature=0.5,
            messages=messages,
        )
        content = (response.choices[0].message.content or "").strip() or FALLBACK_QUESTIONS[question_number - 1]
        return {"content": content, "is_final": False, "question_number": question_number}
    except Exception as e:
        logger.error("OpenAI call failed, using fallback question: %s", e)
        content = FALLBACK_QUESTIONS[question_number - 1]
        return {"content": content, "is_final": False, "question_number": question_number}


def _generate_feedback(history: list[dict]) -> dict:
    if not settings.openai_api_key:
        return {"content": FALLBACK_FEEDBACK, "is_final": True, "question_number": MAX_QUESTIONS}

    try:
        client = OpenAI(api_key=settings.openai_api_key)
        messages = [
            {"role": "system", "content": _build_feedback_system_prompt()},
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