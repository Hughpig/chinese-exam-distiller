from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Callable, Iterable


Question = dict[str, Any]
LLMCaller = Callable[[str], str]

DEFAULT_STRUCTURE_PROMPT = Path("prompts/structure_extract.txt")

_REQUIRED_FIELDS = {
    "id": "",
    "section": "",
    "stem": "",
    "materials": "",
    "answer": "",
    "analysis": "",
    "score_points": [],
    "score": "",
    "question_form": "",
    "skill_type": "",
    "skill_reason": "",
}


def load_prompt(prompt_path: str | Path = DEFAULT_STRUCTURE_PROMPT) -> str:
    return Path(prompt_path).read_text(encoding="utf-8")


def render_structure_prompt(
    paper_text: str,
    prompt_path: str | Path = DEFAULT_STRUCTURE_PROMPT,
) -> str:
    template = load_prompt(prompt_path)
    return template.replace("{paper_text}", paper_text)


def call_openai_compatible(prompt: str) -> str:
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError("缺少 openai 依赖，请先安装 openai。") from exc

    api_key = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("LLM_BASE_URL")
    model = os.getenv("LLM_MODEL", "gpt-4o-mini")

    if not api_key:
        raise RuntimeError("未设置 LLM_API_KEY 或 OPENAI_API_KEY。")

    client = OpenAI(api_key=api_key, base_url=base_url)

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "你是严谨的 JSON 抽取助手。必须只输出合法 JSON。",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0,
    )

    return response.choices[0].message.content or ""


def parse_json_response(text: str) -> Any:
    cleaned = text.strip()

    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    json_text = _extract_json_fragment(cleaned)
    if json_text is None:
        raise ValueError(f"LLM 响应中未找到 JSON：{text[:500]}")

    try:
        return json.loads(json_text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"无法解析 LLM JSON 响应：{exc}\n响应片段：{json_text[:500]}") from exc


def _extract_json_fragment(text: str) -> str | None:
    array_start = text.find("[")
    object_start = text.find("{")

    candidates = []
    if array_start != -1:
        candidates.append((array_start, "[", "]"))
    if object_start != -1:
        candidates.append((object_start, "{", "}"))

    if not candidates:
        return None

    start, _open_char, close_char = min(candidates, key=lambda item: item[0])
    end = text.rfind(close_char)

    if end <= start:
        return None

    return text[start : end + 1]


def normalize_questions(data: Any) -> list[Question]:
    if data is None:
        return []

    if isinstance(data, list):
        return [_normalize_question(item) for item in data if isinstance(item, dict)]

    if isinstance(data, dict):
        if isinstance(data.get("questions"), list):
            return normalize_questions(data["questions"])

        if isinstance(data.get("items"), list):
            return normalize_questions(data["items"])

        if isinstance(data.get("sections"), list):
            questions: list[Question] = []
            for section in data["sections"]:
                if not isinstance(section, dict):
                    continue

                section_name = str(section.get("section") or section.get("name") or "")
                section_materials = str(section.get("materials") or section.get("material") or "")

                for item in section.get("questions", []) or []:
                    if not isinstance(item, dict):
                        continue

                    question = dict(item)
                    question.setdefault("section", section_name)

                    if section_materials and not question.get("materials"):
                        question["materials"] = section_materials

                    questions.append(_normalize_question(question))

            return questions

    raise ValueError("结构化结果必须是题目数组，或包含 questions/items/sections 的对象。")


def _normalize_question(item: dict[str, Any]) -> Question:
    question = dict(_REQUIRED_FIELDS)
    question.update(item)

    for key, default_value in _REQUIRED_FIELDS.items():
        if key == "score_points":
            question[key] = _normalize_score_points(question.get(key))
        elif question.get(key) is None:
            question[key] = default_value
        elif not isinstance(question.get(key), str):
            question[key] = str(question.get(key))

    if not question["skill_type"].strip():
        question["skill_type"] = "未分类"

    return question


def _normalize_score_points(value: Any) -> list[str]:
    if value is None or value == "":
        return []

    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]

    if isinstance(value, str):
        parts = re.split(r"[；;\n]+", value)
        return [part.strip() for part in parts if part.strip()]

    return [str(value).strip()]


def chunk_pages(
    pages: list[str],
    pages_per_chunk: int = 3,
    overlap_pages: int = 1,
) -> list[dict[str, Any]]:
    if pages_per_chunk <= 0:
        raise ValueError("pages_per_chunk 必须大于 0。")

    if overlap_pages < 0:
        raise ValueError("overlap_pages 不能小于 0。")

    if overlap_pages >= pages_per_chunk:
        raise ValueError("overlap_pages 必须小于 pages_per_chunk。")

    chunks: list[dict[str, Any]] = []
    step = pages_per_chunk - overlap_pages
    start = 0

    while start < len(pages):
        end = min(start + pages_per_chunk, len(pages))
        chunk_text = "\n\n".join(
            f"【第{page_number}页】\n{page_text}"
            for page_number, page_text in enumerate(pages[start:end], start=start + 1)
        )

        chunks.append(
            {
                "start_page": start + 1,
                "end_page": end,
                "text": chunk_text,
            }
        )

        if end == len(pages):
            break

        start += step

    return chunks


def structure_text(
    paper_text: str,
    llm_caller: LLMCaller | None = None,
    prompt_path: str | Path = DEFAULT_STRUCTURE_PROMPT,
) -> list[Question]:
    caller = llm_caller or call_openai_compatible
    prompt = render_structure_prompt(paper_text, prompt_path=prompt_path)
    response_text = caller(prompt)
    data = parse_json_response(response_text)
    return normalize_questions(data)


def structure_pages(
    pages: list[str],
    llm_caller: LLMCaller | None = None,
    prompt_path: str | Path = DEFAULT_STRUCTURE_PROMPT,
    pages_per_chunk: int = 3,
    overlap_pages: int = 1,
) -> list[Question]:
    caller = llm_caller or call_openai_compatible
    chunks = chunk_pages(
        pages,
        pages_per_chunk=pages_per_chunk,
        overlap_pages=overlap_pages,
    )

    all_questions: list[Question] = []

    for chunk in chunks:
        prompt = render_structure_prompt(chunk["text"], prompt_path=prompt_path)
        response_text = caller(prompt)
        data = parse_json_response(response_text)
        questions = normalize_questions(data)

        for question in questions:
            question["_source_pages"] = [chunk["start_page"], chunk["end_page"]]
            all_questions.append(question)

    return merge_duplicate_questions(all_questions)


def structure_paper(extracted: Any) -> list[Question]:
    if isinstance(extracted, dict):
        if isinstance(extracted.get("pages"), list):
            pages = [
                str(page.get("text", "") if isinstance(page, dict) else page)
                for page in extracted["pages"]
            ]
            return structure_pages(pages)

        if isinstance(extracted.get("text"), str):
            return structure_text(extracted["text"])

        if isinstance(extracted.get("full_text"), str):
            return structure_text(extracted["full_text"])

    if isinstance(extracted, list):
        pages = [
            str(page.get("text", "") if isinstance(page, dict) else page)
            for page in extracted
        ]
        return structure_pages(pages)

    if isinstance(extracted, str):
        return structure_text(extracted)

    raise ValueError("无法识别 extracted 数据格式。")

PLACEHOLDER_MARKERS = [
    "题目未提供",
    "根据上下文推测",
    "无具体题干",
    "故留空",
]

IMPORTANT_TEXT_FIELDS = [
    "stem",
    "materials",
    "answer",
    "analysis",
    "score",
    "question_form",
    "skill_type",
    "skill_reason",
]


def _text(value) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _is_placeholder_question(question: dict) -> bool:
    combined = "\n".join(
        _text(question.get(key))
        for key in ["stem", "skill_reason", "answer", "analysis"]
    )
    return any(marker in combined for marker in PLACEHOLDER_MARKERS)


def _question_quality_score(question: dict) -> int:
    score = 0

    for field in IMPORTANT_TEXT_FIELDS:
        value = _text(question.get(field))
        if value:
            score += 2

    stem = _text(question.get("stem"))
    answer = _text(question.get("answer"))
    materials = _text(question.get("materials"))
    score_points = question.get("score_points") or []

    if len(stem) >= 10:
        score += 2
    if len(answer) >= 5:
        score += 3
    if len(materials) >= 20:
        score += 1
    if isinstance(score_points, list):
        score += len([item for item in score_points if _text(item)])

    if _text(question.get("skill_type")) == "未分类":
        score -= 8
    if not _text(question.get("question_form")):
        score -= 2
    if not _text(question.get("score")):
        score -= 1
    if _is_placeholder_question(question):
        score -= 15

    return score

def _merge_source_pages(*questions: dict) -> list:
    pages = []

    for question in questions:
        for page in question.get("_source_pages") or []:
            if page not in pages:
                pages.append(page)

    return sorted(pages)

def _unique_texts(items: Iterable[Any]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()

    for item in items:
        text = _text(item)
        if not text or text in seen:
            continue

        seen.add(text)
        result.append(text)

    return result


def _merge_question_fields(primary: dict, secondary: dict) -> dict:
    merged = dict(primary)

    for key, value in secondary.items():
        if key == "_source_pages":
            continue

        current = merged.get(key)

        if isinstance(current, list) and isinstance(value, list):
            merged[key] = _unique_texts([*current, *value])
            continue


        if not _text(current) and _text(value):
            merged[key] = value

    merged["_source_pages"] = _merge_source_pages(primary, secondary)

    return merged


def merge_duplicate_questions(questions: list[dict]) -> list[dict]:
    merged_by_id: dict[str, dict] = {}
    no_id_questions: list[dict] = []

    for question in questions:
        question_id = _text(question.get("id"))

        if not question_id:
            no_id_questions.append(question)
            continue

        existing = merged_by_id.get(question_id)

        if existing is None:
            merged_by_id[question_id] = question
            continue

        existing_score = _question_quality_score(existing)
        current_score = _question_quality_score(question)

        if current_score > existing_score:
            merged_by_id[question_id] = _merge_question_fields(question, existing)
        else:
            merged_by_id[question_id] = _merge_question_fields(existing, question)

    return [*merged_by_id.values(), *no_id_questions]
