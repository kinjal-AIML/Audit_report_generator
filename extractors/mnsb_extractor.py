from docx import Document
import re
from utils.number_to_words import number_to_indian_rupees

def extract_mnsb_data(file_path):

    doc = Document(file_path)

    full_text = "\n".join([
        para.text for para in doc.paragraphs
    ])

    data = {}

    branch_match = re.search(r'Branch:\s*(.*?)\s*Period:', full_text)

    if branch_match:
        data["branch_name"] = branch_match.group(1).strip()

    period_match = re.search(
        r'Period:\s*(\d{2}-\d{2}-\d{4})\s*to\s*(\d{2}-\d{2}-\d{4})',
        full_text
    )

    if period_match:
        data["period_start"] = period_match.group(1)
        data["period_end"] = period_match.group(2)

    # Extract Closing Cash Balance from DOCX
    cash_match = re.search(
        r'Closing Cash Balance\s*:?\s*Rs\.?\s*([\d,]+(?:\.\d{2})?)',
        full_text,
        re.IGNORECASE
    )

    if cash_match:
        balance_str = cash_match.group(1).replace(',', '')
        data["closing_cash_balance"] = balance_str
        data["closing_cash_balance_words"] = number_to_indian_rupees(balance_str)

    # Extract Cash Verification Date
    verification_match = re.search(
        r'Cash Verification Date\s*:?\s*(\d{2}/\d{2}/\d{4})',
        full_text,
        re.IGNORECASE
    )

    if verification_match:
        data["cash_verification_date"] = verification_match.group(1)

    return data