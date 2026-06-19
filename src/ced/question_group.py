from typing import Iterable


GroupedQuestions = dict[str, list[dict]]


def group_questions_by_skill_type(questions: list[dict]) -> dict[str, list[dict]]:
    groups: dict[str, list[dict]] = {}

    for question in questions:
        skill_type = question.get("skill_type", "未分类")
        groups.setdefault(skill_type, []).append(question)

    return groups


def group_questions_by_type(
    structured_data: list[dict],
    *,
    min_questions: int = 1,
    exclude_skill_types: Iterable[str] | None = None,
) -> GroupedQuestions:
    excluded = set(exclude_skill_types or [])
    groups = group_questions_by_skill_type(structured_data)

    return {
        skill_type: questions
        for skill_type, questions in groups.items()
        if skill_type not in excluded and len(questions) >= min_questions
    }
