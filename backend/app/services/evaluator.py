import json
from statistics import mean

from openai import OpenAI

from ..config import settings
from ..schemas import EvaluationResult
from .bars_loader import load_bars_criteria


SYSTEM_PROMPT = """
あなたはITエンジニア面談の評価者です。
面談回答をBARS評価基準に基づいて厳密に評価してください。
出力は必ずJSONのみで返してください。
""".strip()


def _clamp_level(value: int) -> int:
    try:
        value = int(value)
    except (TypeError, ValueError):
        value = 3
    return max(1, min(5, value))


def criteria_prompt_block() -> str:
    criteria = load_bars_criteria()
    lines: list[str] = []

    for criterion in criteria:
        lines.append(f"■ {criterion.label} ({criterion.key})")
        for level in criterion.levels:
            lines.append(f"  Level {level.level}: {level.description}")

    return "\n".join(lines)


def build_user_prompt(question: str, transcript: str) -> str:
    return f"""
以下の面談回答を評価してください。

【質問】
{question}

【回答】
{transcript}

【BARS評価基準】
{criteria_prompt_block()}

【出力要件】
- 必ず1〜5の整数で出力
- overall_level は5項目平均を四捨五入した整数
- summary_comment は120文字以内の日本語
- advice は3件、各40文字以内
- criterion_feedbacks は5件
- key は以下のいずれかのみ
  - japanese_natural
  - nonverbal_natural
  - star_logic
  - technical_depth
  - logic_consistency
- score は各項目の点数と一致させる
- current_issue は「今どこが足りないか」
- feedback_comment は「どう直すか」
- next_action は「次回すぐ実行する1アクション」
- improved_example は「面接でそのまま使える改善後の回答例」
- improved_example は50〜120文字程度
- improved_example は「結論→行動→結果」の流れを意識する
- 抽象表現だけで終わらず、面談で実際に直せる内容にする

{{
  "japanese_natural": 1,
  "nonverbal_natural": 1,
  "star_logic": 1,
  "technical_depth": 1,
  "logic_consistency": 1,
  "overall_level": 1,
  "summary_comment": "",
  "advice": ["", "", ""],
  "criterion_feedbacks": [
    {{
      "key": "japanese_natural",
      "score": 1,
      "current_issue": "",
      "feedback_comment": "",
      "next_action": "",
      "improved_example": ""
    }},
    {{
      "key": "nonverbal_natural",
      "score": 1,
      "current_issue": "",
      "feedback_comment": "",
      "next_action": "",
      "improved_example": ""
    }},
    {{
      "key": "star_logic",
      "score": 1,
      "current_issue": "",
      "feedback_comment": "",
      "next_action": "",
      "improved_example": ""
    }},
    {{
      "key": "technical_depth",
      "score": 1,
      "current_issue": "",
      "feedback_comment": "",
      "next_action": "",
      "improved_example": ""
    }},
    {{
      "key": "logic_consistency",
      "score": 1,
      "current_issue": "",
      "feedback_comment": "",
      "next_action": "",
      "improved_example": ""
    }}
  ]
}}
""".strip()


def fallback_evaluate(question: str, transcript: str) -> EvaluationResult:
    text = transcript.strip()
    length = len(text)
    has_digits = any(ch.isdigit() for ch in text)
    has_because = any(k in text for k in ["なぜ", "理由", "ため", "ので", "だから"])
    has_result = any(k in text for k in ["結果", "改善", "向上", "%", "件", "短縮"])
    has_tech = any(
        k.lower() in text.lower()
        for k in ["java", "spring", "python", "sql", "api", "aws", "docker"]
    )

    japanese_natural = 3 if length > 80 else 2
    nonverbal_natural = 3
    star_logic = 4 if has_result and has_because else 3 if length > 120 else 2
    technical_depth = 4 if has_tech and has_because else 3 if has_tech else 2
    logic_consistency = 4 if len(text.split("。")) >= 3 else 3

    if has_digits:
        star_logic = min(5, star_logic + 1)
        technical_depth = min(5, technical_depth + 1)

    values = [
        japanese_natural,
        nonverbal_natural,
        star_logic,
        technical_depth,
        logic_consistency,
    ]
    overall = round(mean(values))

    advice = [
        "結論を先に置く",
        "結果は数値で示す",
        "技術選定理由まで述べる",
    ]

    criterion_feedbacks = [
        {
            "key": "japanese_natural",
            "score": japanese_natural,
            "current_issue": "表現がやや説明的で、面談向けの簡潔さが弱いです。",
            "feedback_comment": "1文を短くし、結論から先に述べてください。",
            "next_action": "冒頭を『結論から申し上げますと』で始める。",
            "improved_example": "結論から申し上げますと、私はJavaとSpring Bootを用いた業務システム開発を担当し、課題に対して改善施策を実行し、処理時間の短縮につなげました。",
        },
        {
            "key": "nonverbal_natural",
            "score": nonverbal_natural,
            "current_issue": "テキスト入力のため非言語情報は限定評価です。",
            "feedback_comment": "実面談では視線・表情・相づちも意識してください。",
            "next_action": "回答前に一呼吸置いて落ち着いて話す。",
            "improved_example": "結論から申し上げますと、私は落ち着いて簡潔に回答することを意識し、相手に伝わりやすいペースで説明することで、内容を正確に伝えられるよう努めています。",
        },
        {
            "key": "star_logic",
            "score": star_logic,
            "current_issue": "状況・行動・結果の順序がやや弱いです。",
            "feedback_comment": "『状況→課題→行動→結果』の順で整理してください。",
            "next_action": "最後を数値や成果で締める。",
            "improved_example": "JavaとSpring Bootによる社内システム開発で性能課題があったため、SQLの見直しを実施し、その結果、処理時間を約40％短縮しました。",
        },
        {
            "key": "technical_depth",
            "score": technical_depth,
            "current_issue": "技術名だけでなく、選定理由や工夫がもう少し必要です。",
            "feedback_comment": "なぜその技術を使ったかを1文加えてください。",
            "next_action": "『○○を選んだ理由は〜』を入れる。",
            "improved_example": "JavaとSpring Bootを用いて社内業務システムを開発し、性能課題に対してSQLを見直した結果、処理時間を約40％短縮できました。選定理由も含めて説明できます。",
        },
        {
            "key": "logic_consistency",
            "score": logic_consistency,
            "current_issue": "話のつながりはあるが、主張の軸がやや曖昧です。",
            "feedback_comment": "結論と根拠を対応させて説明してください。",
            "next_action": "各回答を3点以内に絞る。",
            "improved_example": "結論から申し上げますと、私は性能改善に強みがあります。実際にSQL見直しを行い、処理時間を約40％短縮したため、その点を根拠として説明できます。",
        },
    ]

    return EvaluationResult(
        japanese_natural=japanese_natural,
        nonverbal_natural=nonverbal_natural,
        star_logic=star_logic,
        technical_depth=technical_depth,
        logic_consistency=logic_consistency,
        overall_level=overall,
        summary_comment="基礎は伝わっています。結論・根拠・成果をより明確にすると評価が上がります。",
        advice=advice,
        criterion_feedbacks=criterion_feedbacks,
    )


def _fallback_preparation(resume_text: str, job_description: str) -> dict:
    return {
        "one_minute_intro": (
            f"これまでの経験を活かし、{job_description[:30]}の業務に貢献できると考えています。"
            "技術力とコミュニケーション力を武器に、チームに早期貢献することを目指しています。"
        ),
        "three_minute_intro": (
            "これまでのキャリアを3つのフェーズでご説明します。\n\n"
            f"【第1フェーズ】エンジニアとしての基礎を習得し、{resume_text[:40]}の経験を積みました。\n\n"
            "【第2フェーズ】より複雑な課題に取り組み、チームリードや設計を担当する機会も得ました。\n\n"
            "【第3フェーズ】直近では技術的な意思決定にも関わり、プロジェクト全体を見渡す視点を養いました。"
        ),
        "matching_points": [
            "経歴書に記載されたスキルが案件の求めるスキルと合致しています",
            "業務ドメインの経験が案件の業種と近い可能性があります",
        ],
        "risk_points": [
            "日本語でのドキュメント作成経験は面談中に確認が必要です",
            "チーム規模や開発プロセスへの適応は入社後の確認が必要です",
        ],
        "expected_questions": [
            {
                "question": "これまでの経歴を簡単に教えてください",
                "intent": "候補者のキャリアの流れと強みの把握",
                "answer_points": [
                    "STAR構造（状況→行動→結果）で話す",
                    "数値実績を必ず含める",
                    "今回の案件との関連性で締める",
                ],
                "caution": "全経歴を時系列で話すと長くなる。直近3年を中心に絞ること",
            },
            {
                "question": "技術的に難しかった課題と、どう乗り越えたかを教えてください",
                "intent": "問題解決能力と技術深度の確認",
                "answer_points": [
                    "課題の背景と影響範囲を明確に説明する",
                    "自分が取ったアプローチと選定理由を述べる",
                    "結果と学びをセットで伝える",
                ],
                "caution": "抽象的な説明で終わらず、具体的な技術名や数値を入れること",
            },
        ],
        "reverse_questions": [
            {
                "question": "チームの技術的な意思決定はどのように行われていますか？",
                "purpose": "技術文化・裁量度の確認",
            },
            {
                "question": "入社後、最初の3ヶ月でどのようなことに取り組むことが多いですか？",
                "purpose": "オンボーディングの実態把握",
            },
        ],
        "preparation_advice": (
            "面談では結論を先に述べるよう意識してください。"
            "技術的な質問には具体的な数値や事例を交えて回答すると説得力が増します。"
            "逆質問は必ず1〜2件準備し、案件への関心を示しましょう。"
        ),
    }


def _gpt_preparation(resume_text: str, job_description: str) -> dict:
    from openai import OpenAI
    client = OpenAI(api_key=settings.openai_api_key)

    system_prompt = (
        "あなたは外国人ITエンジニアの面談前準備を支援するアシスタントです。"
        "経歴書と案件情報をもとに、面談準備シートをJSON形式で出力してください。"
        "出力は必ずJSONのみとし、説明文は不要です。"
    )

    user_prompt = f"""
以下の経歴書と案件情報をもとに、面談前準備シートを作成してください。

【経歴書】
{resume_text}

【案件情報】
{job_description}

【出力形式】
{{
  "one_minute_intro": "案件に合わせた1分自己紹介（文字列）",
  "three_minute_intro": "案件に合わせた3分自己紹介（文字列、改行あり）",
  "matching_points": ["マッチポイント1", "マッチポイント2"],
  "risk_points": ["リスク・確認点1", "リスク・確認点2"],
  "expected_questions": [
    {{
      "question": "想定質問",
      "intent": "出題意図",
      "answer_points": ["回答ポイント1", "回答ポイント2"],
      "caution": "注意点"
    }}
  ],
  "reverse_questions": [
    {{
      "question": "逆質問",
      "purpose": "聞く目的"
    }}
  ],
  "preparation_advice": "面談前アドバイス（文字列）"
}}

要件：
- すべて日本語で出力
- expected_questions は最低3件
- reverse_questions は2〜4件
- matching_points は2〜4件
- risk_points は1〜3件（なければ空配列）
""".strip()

    response = client.chat.completions.create(
        model=settings.openai_model,
        temperature=0.3,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )

    return json.loads(response.choices[0].message.content or "{}")


def generate_interview_preparation(resume_text: str, job_description: str) -> dict:
    if not settings.openai_api_key:
        return _fallback_preparation(resume_text, job_description)
    try:
        return _gpt_preparation(resume_text, job_description)
    except Exception as e:
        import logging
        logging.getLogger(__name__).error("OpenAI call failed, using fallback: %s", e)
        return _fallback_preparation(resume_text, job_description)


def evaluate_interview(question: str, transcript: str) -> EvaluationResult:
    if not settings.openai_api_key:
        return fallback_evaluate(question, transcript)

    try:
        client = OpenAI(api_key=settings.openai_api_key)
        response = client.chat.completions.create(
            model=settings.openai_model,
            temperature=0.2,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": build_user_prompt(question, transcript)},
            ],
        )

        content = response.choices[0].message.content or "{}"
        data = json.loads(content)
        advice = data.get("advice", [])
        criterion_feedbacks = data.get("criterion_feedbacks", [])

        return EvaluationResult(
            japanese_natural=_clamp_level(data.get("japanese_natural", 3)),
            nonverbal_natural=_clamp_level(data.get("nonverbal_natural", 3)),
            star_logic=_clamp_level(data.get("star_logic", 3)),
            technical_depth=_clamp_level(data.get("technical_depth", 3)),
            logic_consistency=_clamp_level(data.get("logic_consistency", 3)),
            overall_level=_clamp_level(data.get("overall_level", 3)),
            summary_comment=data.get("summary_comment", ""),
            advice=[str(item) for item in advice[:3]],
            criterion_feedbacks=[
                {
                    "key": str(item.get("key", "")),
                    "score": _clamp_level(item.get("score", 3)),
                    "current_issue": str(item.get("current_issue", "")),
                    "feedback_comment": str(item.get("feedback_comment", "")),
                    "next_action": str(item.get("next_action", "")),
                    "improved_example": str(item.get("improved_example", "")),
                }
                for item in criterion_feedbacks[:5]
            ],
        )
    except Exception as e:
        import logging
        logging.getLogger(__name__).error("OpenAI call failed, using fallback: %s", e)
        return fallback_evaluate(question, transcript)