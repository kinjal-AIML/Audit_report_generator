import json
from docx import Document


def normalize(text):
    return (
        text.lower()
        .replace("\n", " ")
        .replace(".", "")
        .replace("'", "")
        .strip()
    )


def is_question_header(row):
    texts = [normalize(c.text) for c in row.cells]

    joined = " ".join(texts)

    return (
        "audit review" in joined
        and "comment" in joined
    )


def extract_questions_by_section(doc_path):

    doc = Document(doc_path)

    sections = {}

    for table in doc.tables:

        if len(table.rows) < 3:
            continue

        # -----------------------------------
        # SECTION NAME = ROW 0
        # -----------------------------------

        section_name = table.rows[0].cells[0].text.strip()

        if not section_name:
            continue

        # Skip index table
        if "description" in normalize(section_name):
            continue

        # -----------------------------------
        # HEADER ROW = ROW 1
        # -----------------------------------

        header_row = table.rows[1]

        if not is_question_header(header_row):
            continue

        # -----------------------------------
        # CREATE SECTION
        # -----------------------------------

        if section_name not in sections:
            sections[section_name] = []

        # -----------------------------------
        # DATA ROWS START FROM ROW 2
        # -----------------------------------

        for row in table.rows[2:]:

            cells = [c.text.strip() for c in row.cells]

            if len(cells) < 2:
                continue

            audit_review = cells[1] if len(cells) > 1 else ""

            # skip empty rows
            if not audit_review.strip():
                continue

            item = {
                "sr_no": cells[0] if len(cells) > 0 else "",
                "audit_review": cells[1] if len(cells) > 1 else "",
                "auditor_comment": cells[2] if len(cells) > 2 else "",
                "branch_reply": cells[3] if len(cells) > 3 else ""
            }

            sections[section_name].append(item)

    return sections


if __name__ == "__main__":

    doc_path = r"D:\audit_report_generator\uploads\MNSB Panchot January 26.docx"

    extracted = extract_questions_by_section(doc_path)

    print(json.dumps(extracted, indent=4, ensure_ascii=False))