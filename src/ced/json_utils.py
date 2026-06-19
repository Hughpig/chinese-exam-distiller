import json
import re
from pathlib import Path
from typing import Any

from json_repair import repair_json


def extract_json(text: str) -> Any:
    cleaned = text.strip()

    if cleaned.startswith("```json"):
        cleaned = cleaned.removeprefix("```json").removesuffix("```").strip()
    elif cleaned.startswith("```"):
        cleaned = cleaned.removeprefix("```").removesuffix("```").strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    match = re.search(r"(\{.*\}|\[.*\])", cleaned, re.S)
    if match:
        cleaned = match.group(1)

    repaired = repair_json(cleaned)
    return json.loads(repaired)


def write_json(data: Any, output_path: str) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def read_json(input_path: str) -> Any:
    return json.loads(Path(input_path).read_text(encoding="utf-8"))
