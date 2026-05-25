from docx import Document
import re


def extract_cnsb_data(file_path):

    doc = Document(file_path)

    full_text = "\n".join([
        para.text for para in doc.paragraphs
    ])

    data = {}

    # Extract Branch
    branch_match = re.search(r'Branch:\s*(.*?)\s*Period:', full_text)

    if branch_match:
        data["branch_name"] = branch_match.group(1).strip()

    # Extract Period
    period_match = re.search(
        r'Period:\s*(\d{2}-\d{2}-\d{4})\s*to\s*(\d{2}-\d{2}-\d{4})',
        full_text
    )

    if period_match:
        data["period_start"] = period_match.group(1)
        data["period_end"] = period_match.group(2)

    # Extract Cash Balance
    cash_match = re.search(
        r'Closing Cash Balance\s*:?\s*Rs\.([\d,]+)',
        full_text
    )

    if cash_match:
        data["closing_cash_balance"] = cash_match.group(1)

    return data