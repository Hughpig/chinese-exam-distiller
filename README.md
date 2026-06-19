# Chinese Exam Distiller

Chinese Exam Distiller is an open-source data engineering toolkit for turning Chinese exam PDFs into structured question data and distilled high-score answering skills.

The core idea is:

```text
PDF exam paper
  → extracted text
  → structured questions
  → questions grouped by skill_type
  → distilled skill JSON
  → optional Markdown study guide
```

## Features

- Extract text from text-based Chinese exam PDFs
- Convert raw exam text into structured question JSON with LLMs
- Classify questions by `skill_type`, such as 文言句子翻译, 古诗情感赏析, 描写方法及作用
- Distill reusable answering skills from questions, answers, analyses, and scoring points
- Store distilled skills as structured JSON for search, reuse, and future training
- Render distilled skills into human-readable Markdown study guides
- Use OpenAI-compatible APIs, including OpenAI, DeepSeek, and other providers

## What Is a Skill?

In this project, a skill is a structured learning object distilled from a group of similar exam questions.

A `skill_type` is the label attached to each question:

```json
{
  "id": "12",
  "stem": "把第②段画线句译成现代汉语。",
  "skill_type": "文言句子翻译"
}
```

A distilled skill is the reusable strategy generated from all questions with the same `skill_type`:

```json
{
  "skill_type": "文言句子翻译",
  "description": "在理解文言实词、虚词、特殊句式及语境的基础上，准确、通顺地转换为现代汉语。",
  "common_questions": [
    "把第②段画线句译成现代汉语。",
    "将文中画线的句子翻译成现代汉语。"
  ],
  "framework": "审清语境 → 切分意群 → 逐词对译 → 调整语序 → 补足省略 → 通顺润色 → 检查得分点",
  "steps": [],
  "templates": [],
  "pitfalls": [],
  "examples": []
}
```

JSON is the source of truth for a skill. Markdown is only a presentation format generated from the skill JSON.

## Quick Start

```bash
pip install -e .
cp .env.example .env
```

Put PDF files into:

```text
data/raw_pdf/
```

Run the full pipeline:

```bash
ced pipeline data/raw_pdf/sample.pdf --name sample
```

Or run step by step:

```bash
ced extract data/raw_pdf/sample.pdf --output-path data/extracted_text/sample.json
ced structure data/extracted_text/sample.json --output-path data/structured_json/sample.json
ced group data/structured_json/sample.json --output-path data/grouped_questions/sample.json
ced distill data/grouped_questions/sample.json --output-path data/distilled_skills/sample.json
```

## Pipeline Outputs

```text
data/extracted_text/      Raw text extracted from PDF
data/structured_json/     Structured exam questions with skill_type labels
data/grouped_questions/   Questions grouped by skill_type
data/distilled_skills/    Distilled skill JSON files
data/study_guides/        Optional Markdown study guides rendered from skill JSON
```

## Data Flow

### 1. Extract

Extract text from a text-based PDF.

```bash
ced extract data/raw_pdf/sample.pdf --output-path data/extracted_text/sample.json
```

### 2. Structure

Use an LLM to convert extracted text into normalized question JSON.

```bash
ced structure data/extracted_text/sample.json --output-path data/structured_json/sample.json
```

Each question contains fields such as:

```json
{
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
  "skill_reason": ""
}
```

### 3. Group

Group structured questions by `skill_type`.

```bash
ced group data/structured_json/sample.json --output-path data/grouped_questions/sample.json
```

### 4. Distill

Distill each question group into reusable answering skills.

```bash
ced distill data/grouped_questions/sample.json --output-path data/distilled_skills/sample.json
```

The distilled JSON is designed for downstream search, recommendation, review planning, dataset generation, or Markdown rendering.

## Environment Variables

```env
LLM_API_KEY=your_api_key
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o-mini
```

`LLM_API_KEY` can also be replaced by `OPENAI_API_KEY`.

## Scope

This project currently supports text-based PDFs only. OCR support may be added later.

The current focus is Chinese exam papers, especially language/literature exams where questions can be distilled into reusable answering skills.

## License

MIT