import json
from pathlib import Path

import fitz


def extract_pdf_text(pdf_path: str | Path) -> dict:
    pdf_path = Path(pdf_path)
    doc = fitz.open(pdf_path)

    pages = []
    for page_index, page in enumerate(doc, start=1):
        pages.append({
            "page": page_index,
            "text": page.get_text("text").strip()
        })

    return {
        "source_file": pdf_path.name,
        "page_count": len(pages),
        "pages": pages
    }


def save_extracted_text(data: dict, output_path: str | Path) -> None:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    output_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
