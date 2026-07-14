#!/usr/bin/env python3
"""Extract final-visible copy and review metadata from a DOCX."""

from __future__ import annotations

import argparse
import json
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
R = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
PKG_REL = "{http://schemas.openxmlformats.org/package/2006/relationships}"


def read_xml(archive: zipfile.ZipFile, name: str) -> ET.Element | None:
    try:
        return ET.fromstring(archive.read(name))
    except KeyError:
        return None


def style_names(styles_root: ET.Element | None) -> dict[str, str]:
    if styles_root is None:
        return {}
    names: dict[str, str] = {}
    for style in styles_root.findall(f".//{W}style"):
        style_id = style.get(f"{W}styleId", "")
        name = style.find(f"{W}name")
        names[style_id] = name.get(f"{W}val", style_id) if name is not None else style_id
    return names


def relationships(rels_root: ET.Element | None) -> dict[str, str]:
    if rels_root is None:
        return {}
    return {
        rel.get("Id", ""): rel.get("Target", "")
        for rel in rels_root.findall(f".//{PKG_REL}Relationship")
    }


def visible_text(node: ET.Element) -> str:
    parts: list[str] = []

    def walk(element: ET.Element, deleted: bool = False) -> None:
        tag = element.tag
        now_deleted = deleted or tag in {f"{W}del", f"{W}moveFrom"}
        if tag == f"{W}t" and not now_deleted:
            parts.append(element.text or "")
        elif tag == f"{W}tab" and not now_deleted:
            parts.append("\t")
        elif tag in {f"{W}br", f"{W}cr"} and not now_deleted:
            parts.append("\n")
        for child in element:
            walk(child, now_deleted)

    walk(node)
    text = "".join(parts)
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def paragraph_style(paragraph: ET.Element, names: dict[str, str]) -> str:
    style = paragraph.find(f"./{W}pPr/{W}pStyle")
    if style is None:
        return "Normal"
    style_id = style.get(f"{W}val", "")
    return names.get(style_id, style_id or "Normal")


def markdown_paragraph(paragraph: ET.Element, names: dict[str, str]) -> str:
    text = visible_text(paragraph)
    if not text:
        return ""
    style = paragraph_style(paragraph, names)
    match = re.search(r"heading\s*([1-6])", style, flags=re.IGNORECASE)
    if match:
        return f"{'#' * int(match.group(1))} {text}"
    if style.lower() in {"title", "subtitle"}:
        prefix = "#" if style.lower() == "title" else "##"
        return f"{prefix} {text}"
    numbering = paragraph.find(f"./{W}pPr/{W}numPr")
    if numbering is not None:
        return f"- {text}"
    return text


def table_markdown(table: ET.Element, names: dict[str, str]) -> str:
    rows: list[list[str]] = []
    for row in table.findall(f"./{W}tr"):
        cells: list[str] = []
        for cell in row.findall(f"./{W}tc"):
            paragraphs = [
                markdown_paragraph(p, names).lstrip("#- ").strip()
                for p in cell.findall(f".//{W}p")
            ]
            cells.append("<br>".join(part for part in paragraphs if part).replace("|", "\\|"))
        rows.append(cells)
    if not rows:
        return ""
    width = max(len(row) for row in rows)
    rows = [row + [""] * (width - len(row)) for row in rows]
    header = rows[0]
    output = ["| " + " | ".join(header) + " |", "| " + " | ".join(["---"] * width) + " |"]
    output.extend("| " + " | ".join(row) + " |" for row in rows[1:])
    return "\n".join(output)


def extract(input_path: Path, markdown_path: Path, report_path: Path) -> None:
    with zipfile.ZipFile(input_path) as archive:
        document = read_xml(archive, "word/document.xml")
        if document is None:
            raise ValueError("word/document.xml is missing")
        names = style_names(read_xml(archive, "word/styles.xml"))
        rels = relationships(read_xml(archive, "word/_rels/document.xml.rels"))
        comments = read_xml(archive, "word/comments.xml")
        body = document.find(f"./{W}body")
        blocks: list[str] = []
        if body is not None:
            for child in body:
                if child.tag == f"{W}p":
                    block = markdown_paragraph(child, names)
                elif child.tag == f"{W}tbl":
                    block = table_markdown(child, names)
                else:
                    block = ""
                if block:
                    blocks.append(block)

        comment_rows: list[dict[str, str]] = []
        if comments is not None:
            for comment in comments.findall(f".//{W}comment"):
                comment_rows.append(
                    {
                        "id": comment.get(f"{W}id", ""),
                        "author": comment.get(f"{W}author", ""),
                        "date": comment.get(f"{W}date", ""),
                        "text": visible_text(comment),
                    }
                )

        report = {
            "source": str(input_path),
            "paragraphs": len(document.findall(f".//{W}p")),
            "tables": len(document.findall(f".//{W}tbl")),
            "tracked_insertions": len(document.findall(f".//{W}ins")),
            "tracked_deletions": len(document.findall(f".//{W}del")),
            "comments": comment_rows,
            "external_links": sorted(
                target for target in rels.values() if target.startswith(("http://", "https://"))
            ),
        }

    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.write_text("\n\n".join(blocks) + "\n", encoding="utf-8")
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--markdown", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    extract(args.input, args.markdown, args.report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
