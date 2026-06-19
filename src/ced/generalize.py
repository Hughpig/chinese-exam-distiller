from pathlib import Path
from typing import Any
import json

from ced.llm_client import LLMClient

PROMPTS_DIR = Path(__file__).resolve().parent.parent.parent / "prompts"


def load_prompt(name: str) -> str:
    return (PROMPTS_DIR / name).read_text(encoding="utf-8")


GENERALIZE_SYSTEM_PROMPT = load_prompt("generalize_skill_system.txt")


def build_generalize_prompt(manual: dict[str, Any]) -> str:
    template = load_prompt("generalize_skill_user.txt")
    manual_json = json.dumps(manual, ensure_ascii=False, indent=2)
    return template.replace("{manual_json}", manual_json)


def normalize_manuals(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]

    if isinstance(data, dict):
        for key in ("skills", "manuals", "distilled_skills"):
            value = data.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]

        return [data]

    raise ValueError("Unsupported distilled skills format.")


def generalize_skill(
    manual: dict[str, Any],
    client: LLMClient | None = None,
) -> dict[str, Any]:
    client = client or LLMClient()

    prompt = f"""{GENERALIZE_SYSTEM_PROMPT}

{build_generalize_prompt(manual)}
"""

    skill = client.chat_json(prompt)

    if "source_manual" not in skill:
        skill["source_manual"] = {
            "skill_type": manual.get("skill_type") or manual.get("type") or manual.get("name")
        }

    return skill


def generalize_all_manuals(data: Any) -> dict[str, Any]:
    manuals = normalize_manuals(data)
    client = LLMClient()

    skills = [
        generalize_skill(manual, client=client)
        for manual in manuals
    ]

    return {
        "skills": skills,
    }
