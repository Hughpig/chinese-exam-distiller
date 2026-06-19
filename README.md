# Chinese Exam Distiller

Chinese Exam Distiller is an open-source data engineering toolkit for turning Chinese exam PDFs into structured question data and distilled high-score answering skills.

## Features

- Extract text from text-based PDF exam papers
- Convert raw exam text into structured JSON with LLMs
- Group questions by question type
- Distill reusable answering strategies from questions and standard answers
- Use OpenAI-compatible APIs, including OpenAI, DeepSeek, and other providers

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

## Output Files

```text
data/extracted_text/      Raw text extracted from PDF
data/structured_json/     Structured exam questions
data/grouped_questions/   Questions grouped by type
data/distilled_skills/    Distilled answering skills
```

## Environment Variables

```env
LLM_API_KEY=your_api_key
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o-mini
```

## Scope

This project currently supports text-based PDFs only. OCR support may be added later.

## License

MIT