from typing import List, Dict, Any, Optional
import re

try:
    from docx import Document  # type: ignore
    from docx.text.paragraph import Paragraph as DocxParagraph  # type: ignore
    from docx.table import Table as DocxTable  # type: ignore
except Exception:  # pragma: no cover
    Document = None
    DocxParagraph = None  # type: ignore
    DocxTable = None  # type: ignore


_HEADER_STYLE_PREFIXES = ("Heading",)


def _is_heading(paragraph) -> bool:
    if not paragraph or not paragraph.text or not paragraph.text.strip():
        return False
    style_name = getattr(getattr(paragraph, "style", None), "name", "") or ""
    if any(style_name.startswith(pfx) for pfx in _HEADER_STYLE_PREFIXES):
        return True
    txt = paragraph.text.strip()
    if len(txt) >= 6 and txt.isupper():
        return True
    # Bold and centered heuristic
    try:
        if any(r.bold for r in paragraph.runs) and paragraph.alignment in (1, 3):
            return True
    except Exception:
        pass
    return False


def _slug(s: str) -> str:
    s = re.sub(r"[^A-Za-z0-9]+", "_", s.strip())
    s = re.sub(r"_+", "_", s)
    return s.strip("_").lower()


def _norm(s: str) -> str:
    return (s or "").lower().replace("\n", " ").replace(".", "").replace("'", "").strip()


def _table_header(table) -> List[str]:
    if not table.rows:
        return []
    cells = table.rows[0].cells
    return [c.text.strip() or f"Col_{i}" for i, c in enumerate(cells)]


def _is_index_like_headers(headers: List[str]) -> bool:
    lows = [h.strip().lower() for h in headers]
    # Common index/contents/page indicators
    if any(("page" in h) or (h in {"pg", "page no", "page no."}) for h in lows):
        return True
    if any("index" in h for h in lows):
        return True
    if any("contents" in h for h in lows):
        return True
    return False


def _alias_map(name: str) -> str:
    n = name.strip().lower()
    if n in {"sr", "sr.", "sr no", "sr. no.", "sr.no", "s.no", "srno", "sr no.", "sr. no", "sr.no.", "s r no", "s r. no."}:
        return "sr_no"
    if any(k in n for k in [
        "audit review question", "audit question", "question", "questions",
        "audit point", "audit para", "check point", "checkpoint", "verification point",
        "observation", "observations", "query", "subject", "description", "details",
        "particular", "particulars", "matter", "audit review"
    ]):
        return "question"
    if any(k in n for k in [
        "auditor remark", "auditor's remark", "auditor comment", "auditors comment",
        "remark", "remarks", "auditor's comment", "auditors' comment", "comments"
    ]):
        return "remark"
    if any(k in n for k in [
        "reply of branch", "branch reply", "reply", "branch's reply", "branches reply"
    ]):
        return "branch_reply"
    if any(k in n for k in ["annexure reference", "annexure ref", "annexure"]):
        return "annexure_reference"
    return name


def _parse_questions_from_table(table) -> Optional[List[Dict[str, Any]]]:
    headers = _table_header(table)
    if not headers:
        return None
    mapped = [_alias_map(h) for h in headers]
    # Quickly skip obvious non-question listing tables (e.g., Index/Contents)
    if _is_index_like_headers(headers):
        # Only accept if table clearly has supporting audit columns
        if not any(m in ("remark", "branch_reply", "annexure_reference") for m in mapped):
            return None
    # If no explicit 'question' header, choose a likely column by content length
    if "question" not in mapped:
        # Only infer a question column when both remark and branch_reply exist
        support_has_both = ("remark" in mapped) and ("branch_reply" in mapped)
        if not support_has_both:
            return None
        # Compute average text length per column from first 10 data rows
        col_scores = [0] * len(mapped)
        sample_rows = list(table.rows[1:11])
        for row in sample_rows:
            cells = row.cells
            for i in range(min(len(cells), len(col_scores))):
                txt = (cells[i].text or "").strip()
                col_scores[i] += len(txt)
        # Penalize known non-question columns
        for i, m in enumerate(mapped):
            if m in ("sr_no", "remark", "branch_reply", "annexure_reference"):
                col_scores[i] = -1
        if any(s > 0 for s in col_scores):
            candidate = max(range(len(col_scores)), key=lambda i: col_scores[i])
            mapped[candidate] = "question"
        else:
            return None
    out: List[Dict[str, Any]] = []
    for row in table.rows[1:]:
        vals = [c.text.strip() for c in row.cells]
        # pad/trim
        if len(vals) < len(mapped):
            vals += [""] * (len(mapped) - len(vals))
        elif len(vals) > len(mapped):
            vals = vals[: len(mapped)]
        item: Dict[str, Any] = {
            "sr_no": None,
            "question": "",
            "remark": "",
            "branch_reply": "",
            "annexure_reference": "",
        }
        for k, v in zip(mapped, vals):
            if k in item:
                item[k] = v
        # normalize sr_no
        try:
            if item["sr_no"] in (None, ""):
                pass
            else:
                item["sr_no"] = int(re.sub(r"[^0-9]", "", str(item["sr_no"])) or 0)
        except Exception:
            item["sr_no"] = None
        # skip empty questions
        if not (item.get("question") or "annexure" in (item.get("remark", "").lower())):
            continue
        # key derived from question text
        item["key"] = _slug(item.get("question") or f"q_{len(out)+1}")
        out.append(item)
    return out or None


def _parse_section_style_table(table) -> Optional[Dict[str, Any]]:
    """
    Supports templates where:
    - Row 0, Col 0 = section name (e.g., "Cash / Postages / Adhesive Stamps")
    - Row 1 = header row that includes "Audit Review" and "Comment" tokens
    - Data rows start from Row 2; columns [0..3] map to sr_no, audit_review, auditor_comment, branch_reply
    Returns a dict with 'section_name' and 'questions' if recognized, else None.
    """
    try:
        if len(table.rows) < 3:
            return None
        sec_name = (table.rows[0].cells[0].text or "").strip()
        if not sec_name:
            return None
        # Skip obvious index/contents tables
        if "description" in _norm(sec_name):
            return None

        header_texts = [c.text for c in table.rows[1].cells]
        joined = _norm(" ".join(header_texts))
        if not ("audit review" in joined and "comment" in joined):
            return None

        questions: List[Dict[str, Any]] = []
        for row in table.rows[2:]:
            cells = [c.text.strip() for c in row.cells]
            if len(cells) < 2:
                continue
            audit_review = cells[1] if len(cells) > 1 else ""
            if not audit_review.strip():
                continue
            sr = cells[0] if len(cells) > 0 else ""
            auditor_comment = cells[2] if len(cells) > 2 else ""
            branch_reply = cells[3] if len(cells) > 3 else ""

            item: Dict[str, Any] = {
                "sr_no": sr,
                "question": audit_review,
                "remark": auditor_comment,
                "branch_reply": branch_reply,
                "annexure_reference": "",
            }
            item["key"] = _slug(item.get("question") or f"q_{len(questions)+1}")
            # Attempt to normalize sr_no as integer when possible
            try:
                sr_digits = re.sub(r"[^0-9]", "", str(sr))
                item["sr_no"] = int(sr_digits) if sr_digits else sr
            except Exception:
                pass
            questions.append(item)

        return {"section_name": sec_name, "questions": questions} if questions else None
    except Exception:
        return None


def parse_docx_template(file_path: str) -> Dict[str, Any]:
    if not Document:
        return {"sections": []}
    doc = Document(file_path)

    sections: List[Dict[str, Any]] = []

    # Pass 1: Prefer section-style tables (row0=section, row1=headers), as per user's script
    sec_idx = 0
    for tbl in getattr(doc, "tables", []) or []:
        parsed = _parse_section_style_table(tbl)
        if parsed and parsed.get("questions"):
            sec_idx += 1
            sections.append({
                "section_id": f"sec_{sec_idx}",
                "section_name": parsed["section_name"],
                "section_type": "docx_section",
                "questions": parsed["questions"],
            })

    # If nothing found, fallback to mixed-content parsing with heuristic headers
    if not sections and DocxParagraph is not None and DocxTable is not None:
        body = doc.element.body  # CT_Body
        current: Optional[Dict[str, Any]] = None
        for el in body.iterchildren():
            tag = el.tag.rsplit('}', 1)[-1]
            if tag == 'p':
                p = DocxParagraph(el, doc)
                if _is_heading(p):
                    sec_idx += 1
                    title = p.text.strip()
                    current = {
                        "section_id": f"sec_{sec_idx}",
                        "section_name": title,
                        "section_type": "docx_section",
                        "questions": [],
                    }
                    sections.append(current)
            elif tag == 'tbl':
                t = DocxTable(el, doc)
                qs = _parse_questions_from_table(t)
                if qs:
                    if current is None:
                        sec_idx += 1
                        current = {
                            "section_id": f"sec_{sec_idx}",
                            "section_name": f"Section {sec_idx}",
                            "section_type": "docx_section",
                            "questions": [],
                        }
                        sections.append(current)
                    current["questions"].extend(qs)

    sections = [s for s in sections if s.get("questions")]
    return {"sections": sections}
