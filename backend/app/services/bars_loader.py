from functools import lru_cache
import openpyxl
from ..config import settings
from ..schemas import BarsCriterion, CriterionLevel

KEY_MAP = {
    "①日本語の自然さ": "japanese_natural",
    "②日本語の自然さ（非言語）": "nonverbal_natural",
    "③STAR構造（論理性）": "star_logic",
    "④技術説明の深さ": "technical_depth",
    "⑤論理性（一貫性）": "logic_consistency",
}


@lru_cache(maxsize=1)
def load_bars_criteria() -> list[BarsCriterion]:
    wb = openpyxl.load_workbook(settings.bars_excel_path)
    ws = wb.active
    criteria: list[BarsCriterion] = []

    for row in ws.iter_rows(min_row=2, values_only=True):
        label = row[0]
        if not label:
            continue
        key = KEY_MAP[label]
        levels = [CriterionLevel(level=i, description=row[i]) for i in range(1, 6)]
        criteria.append(BarsCriterion(key=key, label=label, levels=levels))
    return criteria


def criteria_prompt_block() -> str:
    blocks: list[str] = []
    for criterion in load_bars_criteria():
        block_lines = [f"- {criterion.label} ({criterion.key})"]
        for item in criterion.levels:
            block_lines.append(f"  Level {item.level}: {item.description}")
        blocks.append("\n".join(block_lines))
    return "\n\n".join(blocks)
