from pathlib import Path
from typing import Any


VALID_RENDER_MODES = {"brief", "normal", "detailed"}

DEFAULT_BRIEF_SKILL_TYPES = {
    "名句默写与诗文积累",
    "字音字形与词语运用",
    "成语使用与病句辨析",
    "文学文化常识",
    "名著情节识记",
}

DEFAULT_DETAILED_SKILL_TYPES = {
    "概括文章内容",
    "梳理情节脉络",
    "人物形象分析",
    "人物心理分析",
    "句子含义理解",
    "句子作用分析",
    "语言赏析",
    "描写方法及作用",
    "修辞手法及作用",
    "标题含义与作用",
    "开头作用分析",
    "结尾作用分析",
    "段落作用分析",
    "线索作用分析",
    "主旨情感概括",
    "表现手法赏析",
    "说明方法及作用",
    "说明文语言准确性",
    "中心论点概括",
    "论证方法及作用",
    "论证思路分析",
    "文言句子翻译",
    "文言内容理解",
    "文言人物形象分析",
    "古诗情感赏析",
    "古诗炼字赏析",
    "古诗表现手法赏析",
    "作文审题立意",
    "作文选材构思",
}


def _as_list(value: Any) -> list:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    return str(value).strip()


def _limit(items: list[str], count: int) -> list[str]:
    return items[:count] if count > 0 else items


def _bullet_lines(items: Any, limit: int = 0) -> list[str]:
    lines = []

    for item in _as_list(items):
        text = _text(item)
        if text:
            lines.append(f"- {text}")

    return _limit(lines, limit)


def _numbered_lines(items: Any, limit: int = 0) -> list[str]:
    lines = []

    for item in _as_list(items):
        text = _text(item)
        if text:
            lines.append(f"{len(lines) + 1}. {text}")

    return _limit(lines, limit)


def _section(title: str, lines: list[str]) -> list[str]:
    if not lines:
        return []
    return [f"### {title}", "", *lines, ""]


def _contains_any(text: str, keywords: set[str]) -> bool:
    return any(keyword and keyword in text for keyword in keywords)


def _dict_value_text(item: dict, keys: list[str]) -> str:
    for key in keys:
        value = _text(item.get(key))
        if value:
            return value
    return ""


def _subskill_lines(items: Any) -> list[str]:
    lines = []

    for item in _as_list(items):
        if isinstance(item, dict):
            name = _dict_value_text(item, ["name", "skill_name", "title"])
            description = _dict_value_text(item, ["description", "summary"])
            behavior = _dict_value_text(item, ["observable_behavior", "behavior", "表现"])

            if name and description and behavior:
                lines.append(f"- {name}：{description}（表现：{behavior}）")
            elif name and description:
                lines.append(f"- {name}：{description}")
            elif name:
                lines.append(f"- {name}")
            continue

        text = _text(item)
        if text:
            lines.append(f"- {text}")

    return lines


def _exam_application_lines(items: Any) -> list[str]:
    lines = []

    for item in _as_list(items):
        if isinstance(item, dict):
            source = _dict_value_text(item, ["source_skill_type", "source", "题型"])
            forms = _first_present_list(item, ["common_question_forms", "question_forms", "常见问法"])
            patterns = _first_present_list(item, ["answering_patterns", "patterns", "答题模式"])

            parts = []
            if forms:
                parts.append("常见问法：" + "；".join(_text(form) for form in forms if _text(form)))
            if patterns:
                parts.append("答题路径：" + "；".join(_text(pattern) for pattern in patterns if _text(pattern)))

            if source and parts:
                lines.append(f"- {source}：" + "；".join(parts))
            elif source:
                lines.append(f"- {source}")
            elif parts:
                lines.append("- " + "；".join(parts))
            continue

        text = _text(item)
        if text:
            lines.append(f"- {text}")

    return lines


def _normalize_mode(mode: str) -> str:
    mode = _text(mode).lower() or "normal"

    if mode not in VALID_RENDER_MODES:
        valid_modes = ", ".join(sorted(VALID_RENDER_MODES))
        raise ValueError(f"Invalid render mode: {mode}. Expected one of: {valid_modes}")

    return mode


def _normalize_keywords(
    keywords: set[str] | list[str] | tuple[str, ...] | str | None,
    defaults: set[str],
) -> set[str]:
    if keywords is None:
        return set(defaults)

    if isinstance(keywords, str):
        return {item.strip() for item in keywords.split(",") if item.strip()}

    return {_text(item) for item in keywords if _text(item)}


def _resolve_mode(
    skill_type: str,
    default_mode: str,
    brief_skill_types: set[str],
    detailed_skill_types: set[str],
) -> str:
    if _contains_any(skill_type, detailed_skill_types):
        return "detailed"

    if _contains_any(skill_type, brief_skill_types):
        return "brief"

    return default_mode


def _get_skill_type(skill: dict, index: int) -> str:
    return (
        _text(skill.get("skill_type"))
        or _text(skill.get("skill_name"))
        or _text(skill.get("type"))
        or _text(skill.get("name"))
        or _text(skill.get("question_type"))
        or _text(skill.get("skill_id"))
        or f"考点 {index}"
    )


def _first_present_text(skill: dict, keys: list[str]) -> str:
    for key in keys:
        value = _text(skill.get(key))
        if value:
            return value
    return ""


def _first_present_list(skill: dict, keys: list[str]) -> list:
    for key in keys:
        items = _as_list(skill.get(key))
        if any(_text(item) for item in items):
            return items
    return []


def _first_sentence(value: Any) -> str:
    text = _text(value)
    if not text:
        return ""

    for separator in ["。", "；", ";", "\n"]:
        if separator in text:
            suffix = "。" if separator == "。" else ""
            return text.split(separator, 1)[0].strip() + suffix

    return text


def _compact_core_ability(skill: dict) -> str:
    core_ability = _first_sentence(
        _first_present_text(
            skill,
            [
                "core_ability",
                "transferable_ability",
                "what_it_tests",
                "exam_focus",
                "description",
                "summary",
                "这类题在考什么",
            ],
        )
    )
    if core_ability:
        return core_ability

    common_forms = _first_present_list(
        skill,
        [
            "common_question_forms",
            "common_questions",
            "question_forms",
            "常见问法",
        ],
    )
    first_form = _text(common_forms[0]) if common_forms else ""
    if first_form:
        return first_form

    return "识别题干要求，调用对应阅读方法、知识规则或答题模板，准确作答。"


def _compact_method(skill: dict) -> list[str]:
    steps = _numbered_lines(
        _first_present_list(
            skill,
            [
                "step_by_step_method",
                "steps",
                "method_steps",
                "solving_steps",
                "解题步骤",
            ],
        ),
        limit=3,
    )
    if steps:
        return steps

    framework = _first_present_text(
        skill,
        [
            "answering_framework",
            "answer_framework",
            "template",
            "答题框架",
        ],
    )
    if framework:
        parts = [
            part.strip()
            for part in framework.replace("→", "，").replace("；", "，").split("，")
            if part.strip()
        ]
        return [f"{index}. {part}" for index, part in enumerate(parts[:3], start=1)]

    return [
        "1. 审清题干中的作答对象和限定角度。",
        "2. 回到文本或知识点中寻找依据。",
        "3. 按“判断 + 分析 + 效果/情感/作用”的结构组织答案。",
    ]


def _compact_mistakes(skill: dict) -> list[str]:
    mistakes = _bullet_lines(
        _first_present_list(
            skill,
            [
                "common_mistakes",
                "mistakes",
                "pitfalls",
                "易错点",
            ],
        ),
        limit=2,
    )
    if mistakes:
        return mistakes

    expressions = _bullet_lines(
        _first_present_list(
            skill,
            [
                "high_score_expressions",
                "expressions",
                "高分表达",
            ],
        ),
        limit=2,
    )
    if expressions:
        return expressions

    return [
        "- 只写结论，不结合文本或题干要求分析。",
        "- 答案缺少关键词，表达笼统，得分点不完整。",
    ]


def _example_mapping_lines(skill: dict, limit: int = 3) -> list[str]:
    lines = []

    examples = _first_present_list(
        skill,
        [
            "example_mapping",
            "examples",
            "sample_questions",
            "例题分析",
        ],
    )

    for item in examples[:limit]:
        if isinstance(item, dict):
            original_question = (
                _text(item.get("original_question"))
                or _text(item.get("question"))
                or _text(item.get("stem"))
            )
            standard_answer = (
                _text(item.get("standard_answer"))
                or _text(item.get("answer"))
                or _text(item.get("analysis"))
            )
            extracted_pattern = (
                _text(item.get("extracted_pattern"))
                or _text(item.get("pattern"))
                or _text(item.get("transferable_method"))
            )

            if original_question:
                lines.append(f"- 原题：{original_question}")
            if standard_answer:
                lines.append(f"  - 答案规律：{standard_answer}")
            if extracted_pattern:
                lines.append(f"  - 可迁移方法：{extracted_pattern}")
            continue

        text = _text(item)
        if text:
            lines.append(f"- {text}")

    return lines


def _render_brief_skill_card(skill: dict, index: int) -> list[str]:
    skill_type = _get_skill_type(skill, index)

    lines = [f"## {index}. {skill_type}", ""]
    lines.extend(_section("考什么", [_compact_core_ability(skill)]))
    lines.extend(_section("怎么做", _compact_method(skill)))
    lines.extend(_section("易错点", _compact_mistakes(skill)))

    return lines


def _render_normal_skill_card(skill: dict, index: int) -> list[str]:
    skill_type = _get_skill_type(skill, index)

    core_ability = _first_present_text(
        skill,
        [
            "core_ability",
            "what_it_tests",
            "exam_focus",
            "这类题在考什么",
        ],
    )
    framework = _first_present_text(
        skill,
        [
            "answering_framework",
            "answer_framework",
            "答题框架",
        ],
    )

    lines = [f"## {index}. {skill_type}", ""]

    if core_ability:
        lines.extend(["### 这类题在考什么", "", core_ability, ""])

    lines.extend(
        _section(
            "常见问法",
            _bullet_lines(
                _first_present_list(
                    skill,
                    [
                        "common_question_forms",
                        "common_questions",
                        "question_forms",
                        "常见问法",
                    ],
                ),
                limit=4,
            ),
        )
    )

    if framework:
        lines.extend(["### 答题框架", "", framework, ""])

    lines.extend(
        _section(
            "解题步骤",
            _numbered_lines(
                _first_present_list(
                    skill,
                    [
                        "step_by_step_method",
                        "steps",
                        "method_steps",
                        "solving_steps",
                        "解题步骤",
                    ],
                ),
                limit=5,
            ),
        )
    )
    lines.extend(
        _section(
            "答题模板",
            _bullet_lines(
                _first_present_list(
                    skill,
                    [
                        "answer_templates",
                        "templates",
                        "答题模板",
                    ],
                ),
                limit=3,
            ),
        )
    )
    lines.extend(
        _section(
            "高分表达",
            _bullet_lines(
                _first_present_list(
                    skill,
                    [
                        "high_score_expressions",
                        "expressions",
                        "高分表达",
                    ],
                ),
                limit=3,
            ),
        )
    )
    lines.extend(
        _section(
            "易错点",
            _bullet_lines(
                _first_present_list(
                    skill,
                    [
                        "common_mistakes",
                        "mistakes",
                        "pitfalls",
                        "易错点",
                    ],
                ),
                limit=3,
            ),
        )
    )

    return lines


def _render_detailed_skill_card(skill: dict, index: int) -> list[str]:
    skill_type = _get_skill_type(skill, index)

    core_ability = _first_present_text(
        skill,
        [
            "core_ability",
            "what_it_tests",
            "exam_focus",
            "这类题在考什么",
        ],
    )
    framework = _first_present_text(
        skill,
        [
            "answering_framework",
            "answer_framework",
            "答题框架",
        ],
    )

    lines = [f"## {index}. {skill_type}", ""]

    if core_ability:
        lines.extend(["### 这类题在考什么", "", core_ability, ""])

    lines.extend(
        _section(
            "常见问法",
            _bullet_lines(
                _first_present_list(
                    skill,
                    [
                        "common_question_forms",
                        "common_questions",
                        "question_forms",
                        "常见问法",
                    ],
                )
            ),
        )
    )

    if framework:
        lines.extend(["### 答题框架", "", framework, ""])

    lines.extend(
        _section(
            "解题步骤",
            _numbered_lines(
                _first_present_list(
                    skill,
                    [
                        "step_by_step_method",
                        "steps",
                        "method_steps",
                        "solving_steps",
                        "解题步骤",
                    ],
                )
            ),
        )
    )
    lines.extend(
        _section(
            "答题模板",
            _bullet_lines(
                _first_present_list(
                    skill,
                    [
                        "answer_templates",
                        "templates",
                        "答题模板",
                    ],
                )
            ),
        )
    )
    lines.extend(
        _section(
            "高分表达",
            _bullet_lines(
                _first_present_list(
                    skill,
                    [
                        "high_score_expressions",
                        "expressions",
                        "高分表达",
                    ],
                )
            ),
        )
    )
    lines.extend(
        _section(
            "易错点",
            _bullet_lines(
                _first_present_list(
                    skill,
                    [
                        "common_mistakes",
                        "mistakes",
                        "pitfalls",
                        "易错点",
                    ],
                )
            ),
        )
    )
    lines.extend(_section("例题分析", _example_mapping_lines(skill)))

    return lines

def _render_general_skill_card(skill: dict, index: int) -> list[str]:
    skill_name = _get_skill_type(skill, index)

    lines = [f"## {index}. {skill_name}", ""]

    description = _first_present_text(skill, ["description", "summary"])
    transferable_ability = _first_present_text(skill, ["transferable_ability", "core_ability"])

    if description:
        lines.extend(["### 能力说明", "", description, ""])

    if transferable_ability:
        lines.extend(["### 可迁移能力", "", transferable_ability, ""])

    lines.extend(
        _section(
            "前置基础",
            _bullet_lines(
                _first_present_list(skill, ["prerequisites", "基础要求", "前置知识"]),
            ),
        )
    )

    lines.extend(
        _section(
            "子能力",
            _subskill_lines(
                _first_present_list(skill, ["subskills", "sub_skills", "子能力"]),
            ),
        )
    )

    lines.extend(
        _section(
            "考试应用",
            _exam_application_lines(
                _first_present_list(skill, ["exam_application", "exam_applications", "应用场景"]),
            ),
        )
    )

    lines.extend(
        _section(
            "学习建议",
            _bullet_lines(
                _first_present_list(skill, ["learning_advice", "study_tips", "practice_suggestions"]),
            ),
        )
    )

    return lines


def _render_skill_card(skill: dict, index: int, mode: str) -> list[str]:
    if skill.get("skill_name") or skill.get("transferable_ability"):
        return _render_general_skill_card(skill, index)

    if mode == "brief":
        return _render_brief_skill_card(skill, index)

    if mode == "detailed":
        return _render_detailed_skill_card(skill, index)

    return _render_normal_skill_card(skill, index)


def _normalize_skills(skills: dict | list) -> list[dict]:
    if isinstance(skills, dict):
        if isinstance(skills.get("skills"), list):
            return [skill for skill in skills["skills"] if isinstance(skill, dict)]

        skill_items = []

        for key, value in skills.items():
            if isinstance(value, dict):
                normalized = dict(value)
                normalized.setdefault("skill_type", _text(key))
                skill_items.append(normalized)

        return skill_items

    return [skill for skill in skills if isinstance(skill, dict)]


def render_skill_markdown(
    skills: dict | list,
    mode: str = "normal",
    brief_types: set[str] | list[str] | tuple[str, ...] | str | None = None,
    detailed_types: set[str] | list[str] | tuple[str, ...] | str | None = None,
) -> str:
    default_mode = _normalize_mode(mode)
    brief_skill_types = _normalize_keywords(brief_types, DEFAULT_BRIEF_SKILL_TYPES)
    detailed_skill_types = _normalize_keywords(detailed_types, DEFAULT_DETAILED_SKILL_TYPES)
    normalized_skills = _normalize_skills(skills)

    lines = [
        "# 语文试卷能力复盘",
        "",
        "这份文档由蒸馏结果自动整理，用于按考点/解题技能复习，而不是按题目外观题型复习。",
        "",
        "## 考点总览",
        "",
    ]

    for index, skill in enumerate(normalized_skills, start=1):
        skill_type = _get_skill_type(skill, index)
        core_ability = _compact_core_ability(skill)
        lines.append(f"- {skill_type}：{core_ability}")

    lines.append("")

    for index, skill in enumerate(normalized_skills, start=1):
        skill_type = _get_skill_type(skill, index)
        resolved_mode = _resolve_mode(
            skill_type,
            default_mode,
            brief_skill_types,
            detailed_skill_types,
        )
        lines.extend(_render_skill_card(skill, index, resolved_mode))

    return "\n".join(lines).rstrip() + "\n"


def save_skill_markdown(
    skills: dict | list,
    output_path: str,
    mode: str = "normal",
    brief_types: set[str] | list[str] | tuple[str, ...] | str | None = None,
    detailed_types: set[str] | list[str] | tuple[str, ...] | str | None = None,
) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        render_skill_markdown(
            skills,
            mode=mode,
            brief_types=brief_types,
            detailed_types=detailed_types,
        ),
        encoding="utf-8",
    )
