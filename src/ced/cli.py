from pathlib import Path

import typer
from rich import print

from ced.distiller import distill_all_groups
from ced.generalize import generalize_all_manuals
from ced.json_utils import read_json, write_json
from ced.pdf_extract import extract_pdf_text, save_extracted_text
from ced.question_group import group_questions_by_type
from ced.structure_parser import structure_paper
from ced.skill_renderer import save_skill_markdown

def parse_csv(value: str | None) -> set[str]:
    if not value:
        return set()
    return {item.strip() for item in value.split(",") if item.strip()}


def filter_ignored_groups(groups, ignore_types: str | None):
    ignored = parse_csv(ignore_types)
    if not ignored:
        return groups

    if isinstance(groups, list):
        return [
            group for group in groups
            if isinstance(group, dict)
            and group.get("skill_type") not in ignored
            and group.get("type") not in ignored
        ]

    if isinstance(groups, dict):
        if "groups" in groups and isinstance(groups["groups"], list):
            return {
                **groups,
                "groups": filter_ignored_groups(groups["groups"], ignore_types),
            }

        return {
            skill_type: group
            for skill_type, group in groups.items()
            if skill_type not in ignored
        }

    return groups



app = typer.Typer(help="Chinese exam PDF distillation toolkit.")


@app.command()
def extract(
    pdf_path: str,
    output_path: str = "data/extracted_text/output.json",
):
    data = extract_pdf_text(pdf_path)
    save_extracted_text(data, output_path)
    print(f"[green]Extracted text saved to {output_path}[/green]")


@app.command()
def structure(
    input_path: str,
    output_path: str = "data/structured_json/output.json",
):
    extracted = read_json(input_path)
    structured = structure_paper(extracted)
    write_json(structured, output_path)
    print(f"[green]Structured paper saved to {output_path}[/green]")


@app.command()
def group(
    input_path: str,
    output_path: str = "data/grouped_questions/output.json",
):
    paper_json = read_json(input_path)
    groups = group_questions_by_type(paper_json)
    write_json(groups, output_path)
    print(f"[green]Grouped questions saved to {output_path}[/green]")


@app.command()
def distill(
    input_path: str,
    output_path: str = "data/distilled_skills/output.json",
    min_questions: int = 1,
    ignore_types: str | None = None,
):
    groups = read_json(input_path)
    groups = filter_ignored_groups(groups, ignore_types)
    skills = distill_all_groups(groups, min_questions=min_questions)
    write_json(skills, output_path)
    print(f"[green]Distilled skills saved to {output_path}[/green]")


@app.command()
def generalize(
    input_path: str,
    output_path: str = "data/general_skills/output.json",
):
    distilled_skills = read_json(input_path)
    general_skills = generalize_all_manuals(distilled_skills)
    write_json(general_skills, output_path)
    print(f"[green]General skills saved to {output_path}[/green]")


@app.command()
def render(
    input_path: str,
    output_path: str = typer.Argument("data/study_guides/output.md"),
    mode: str = "normal",
    brief_types: str | None = None,
    detailed_types: str | None = None,
):
    skills = read_json(input_path)
    save_skill_markdown(
        skills,
        output_path,
        mode=mode,
        brief_types=brief_types,
        detailed_types=detailed_types,
    )
    print(f"[green]Study guide saved to {output_path}[/green]")


@app.command()
def pipeline(
    pdf_path: str,
    name: str | None = None,
    mode: str = "normal",
    brief_types: str | None = None,
    detailed_types: str | None = None,
    min_questions: int = 1,
    ignore_types: str | None = None,
    general_skills: bool = typer.Option(
        False,
        "--general-skills/--no-general-skills",
        help="Generate generalized skills and general study guide. This calls the LLM API.",
    ),
):

    paper_name = name or Path(pdf_path).stem

    extracted_path = f"data/extracted_text/{paper_name}.json"
    structured_path = f"data/structured_json/{paper_name}.json"
    grouped_path = f"data/grouped_questions/{paper_name}.json"
    skills_path = f"data/distilled_skills/{paper_name}.json"
    general_skills_path = f"data/general_skills/{paper_name}.json"
    guide_path = f"data/study_guides/{paper_name}.md"
    general_guide_path = f"data/study_guides/{paper_name}_general.md"


    extracted = extract_pdf_text(pdf_path)
    save_extracted_text(extracted, extracted_path)

    structured = structure_paper(extracted)
    write_json(structured, structured_path)

    groups = group_questions_by_type(structured)
    groups = filter_ignored_groups(groups, ignore_types)
    write_json(groups, grouped_path)

    skills = distill_all_groups(groups, min_questions=min_questions)
    write_json(skills, skills_path)

    save_skill_markdown(
        skills,
        guide_path,
        mode=mode,
        brief_types=brief_types,
        detailed_types=detailed_types,
    )

    if general_skills:
        generalized = generalize_all_manuals(skills)
        write_json(generalized, general_skills_path)

        save_skill_markdown(
            generalized,
            general_guide_path,
            mode=mode,
            brief_types=brief_types,
            detailed_types=detailed_types,
        )



    print("[green]Pipeline completed.[/green]")
    print(f"Extracted: {extracted_path}")
    print(f"Structured: {structured_path}")
    print(f"Grouped: {grouped_path}")
    print(f"Distilled skills: {skills_path}")
    print(f"Study guide: {guide_path}")
    if general_skills:
        print(f"General skills: {general_skills_path}")
        print(f"General study guide: {general_guide_path}")


if __name__ == "__main__":
    app()

