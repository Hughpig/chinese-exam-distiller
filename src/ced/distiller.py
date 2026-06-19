import json
from pathlib import Path

from ced.json_utils import extract_json
from ced.llm_client import LLMClient


def distill_skill_type(
    skill_type: str,
    questions: list[dict],
    prompt_path: str = "prompts/distill_skill.txt",
) -> dict:
    prompt_template = Path(prompt_path).read_text(encoding="utf-8")

    questions_json = json.dumps(questions, ensure_ascii=False, indent=2)

    prompt = (
        prompt_template
        .replace("{skill_type}", skill_type)
        .replace("{questions_json}", questions_json)
    )

    llm = LLMClient()
    response = llm.chat(prompt, temperature=0.3)

    return extract_json(response)


def distill_all_groups(groups: dict, min_questions: int = 1) -> list[dict]:
    results = []

    for skill_type, questions in groups.items():
        if len(questions) < min_questions:
            continue

        skill = distill_skill_type(skill_type, questions)
        results.append(skill)

    return results
