import os
import re
import pdfplumber
import pandas as pd
from pdf2image import convert_from_path
import pytesseract

# ─────────────────────────────────────────────────────────────────────────────
# CHAR-LEVEL WORD RECONSTRUCTION
# ─────────────────────────────────────────────────────────────────────────────
INTRA_WORD_GAP_PX = 3.0
INTER_WORD_GAP_PX = 15.0

def _chars_to_words(chars):
    if not chars:
        return []
    chars_sorted = sorted(chars, key=lambda c: c["x0"])
    tokens = []
    buf = [chars_sorted[0]]
    for c in chars_sorted[1:]:
        gap = c["x0"] - buf[-1]["x1"]
        if gap <= INTRA_WORD_GAP_PX:
            buf.append(c)
        else:
            tokens.append((buf[0]["x0"], buf[-1]["x1"], "".join(ch["text"] for ch in buf)))
            buf = [c]
    tokens.append((buf[0]["x0"], buf[-1]["x1"], "".join(ch["text"] for ch in buf)))
    return tokens

def _page_rows(page, y_group_tolerance=3):
    chars = [c for c in page.chars if c["text"].strip()]
    row_map = {}
    for c in chars:
        key = round(c["top"] / y_group_tolerance) * y_group_tolerance
        row_map.setdefault(key, []).append(c)
    rows = []
    for top in sorted(row_map):
        tokens = _chars_to_words(row_map[top])
        if tokens:
            rows.append((top, tokens))
    return rows

def _all_rows_multipage(pdf_path):
    result = []
    with pdfplumber.open(pdf_path) as pdf:
        for pi, page in enumerate(pdf.pages):
            for top, tokens in _page_rows(page):
                result.append((pi, top, tokens))
    return result

_NOISE = re.compile(
    r"THE MEHSANA|PANCHOT BRANCH|MICR:-|IFSC:-|Print Date|"
    r"^-{5,}$|User Name:|Page \d+ of|^Clerk\s|^Cashier\s|"
    r"Security Details|A/c No\.\s+Name\s+NPA|"
    r"Overdue Report For All|Cash Summary Report|Insurance Pending Register",
    re.IGNORECASE,
)

def _is_noise(text):
    return bool(_NOISE.search(text))

def _token_text(tokens):
    return " ".join(t[2] for t in tokens)

# ─────────────────────────────────────────────────────────────────────────────
# 1. CASH SUMMARY
# ─────────────────────────────────────────────────────────────────────────────
def extract_cash_summary(pdf_path):
    rows = []
    report_date = ""
    all_rows = _all_rows_multipage(pdf_path)
    for _, _, tokens in all_rows:
        line = _token_text(tokens)
        if _is_noise(line):
            continue
        m = re.search(r"AsOn\s+(\S+)", line, re.IGNORECASE)
        if m:
            report_date = m.group(1)
            continue
        m = re.match(r"^(Opening Cash Balance|Total Cash Receipt|Total Cash Payment|Closing Cash Balance)\s+([\d,\.]+)$", line)
        if m:
            rows.append({"Section": "Cash Flow", "Description": m.group(1), "Count": "", "Amount (INR)": m.group(2)})
            continue
        if len(tokens) >= 3:
            last_tok = tokens[-1][2]
            second_last = tokens[-2][2]
            if re.match(r"^[\d,]+\.?\d*$", last_tok) and re.match(r"^\d+$", second_last):
                label = " ".join(t[2] for t in tokens[:-2])
                if any(kw in label.upper() for kw in ["NOTE", "COIN", "PAISA"]):
                    rows.append({"Section": "Denomination Breakup", "Description": label, "Count": second_last, "Amount (INR)": last_tok})
                    continue
        m = re.match(r"^Total:\s*([\d,\.]+)$", line)
        if m:
            rows.append({"Section": "Denomination Breakup", "Description": "TOTAL", "Count": "", "Amount (INR)": m.group(1), "Remarks": "", "Annexure Ref": ""})
            continue
        m = re.search(r"Branch Cash Retention Limit\s*:\s*([\d,\.]+)", line)
        if m:
            rows.append({"Section": "Info", "Description": "Branch Cash Retention Limit", "Count": "", "Amount (INR)": m.group(1), "Remarks": "", "Annexure Ref": ""})
    for row in rows:
        row["Annexure Ref"] = row.get("Annexure Ref", "")
    df = pd.DataFrame(rows, columns=["Section", "Description", "Count", "Amount (INR)", "Remarks", "Annexure Ref"])
    df.attrs["report_date"] = report_date
    return df

# ─────────────────────────────────────────────────────────────────────────────
# 2. INSURANCE PENDING
# ─────────────────────────────────────────────────────────────────────────────
_NPA_CODES = re.compile(r"^(SMA\d|0[0-9]|\d{2}|NPA)$")

def extract_insurance_pending(pdf_path):
    rows = []
    report_date = ""
    branch_code = branch_name = loan_type_code = loan_type_name = ""
    all_rows = _all_rows_multipage(pdf_path)
    for _, _, tokens in all_rows:
        line = _token_text(tokens)
        if not line.strip() or _is_noise(line):
            continue
        m = re.search(r"As On\s*:\s*(\S+)", line, re.IGNORECASE)
        if m:
            report_date = m.group(1)
            continue
        m = re.match(r"^\((\d+)\)\s*-\s*(.+)$", line)
        if m:
            code, name = m.group(1).strip(), m.group(2).strip()
            if code == "004":
                branch_code, branch_name = code, name
            else:
                loan_type_code, loan_type_name = code, name
            continue
        m = re.search(r"(Type Wise Total|Branch Wise Total|Grand Total).+?:\s*(\d+)\s+([\d,\.]+)", line, re.IGNORECASE)
        if m:
            rows.append({"Branch Code": branch_code, "Branch Name": branch_name, "Loan Type Code": "", "Loan Type Name": "", "A/c No.": "", "Name": m.group(1).strip(), "NPA Code": "", "Limit Amount (INR)": m.group(3), "Remarks": f"Count: {m.group(2)}"})
            continue
        if not tokens:
            continue
        acct_tok = tokens[0][2]
        if not re.match(r"^\d{6}$", acct_tok):
            continue
        amt_tok = tokens[-1][2]
        if not re.match(r"^[\d,]+\.?\d*$", amt_tok):
            continue
        npa_code = ""
        name_tokens = []
        for i in range(len(tokens) - 2, 0, -1):
            if _NPA_CODES.match(tokens[i][2]):
                npa_code = tokens[i][2]
                name_tokens = tokens[1:i]
                break
        else:
            name_tokens = tokens[1:-1]
        rows.append({"Branch Code": branch_code, "Branch Name": branch_name, "Loan Type Code": loan_type_code, "Loan Type Name": loan_type_name, "A/c No.": acct_tok, "Name": " ".join(t[2] for t in name_tokens), "NPA Code": npa_code, "Limit Amount (INR)": amt_tok, "Remarks": "", "Annexure Ref": ""})
    for row in rows:
        row["Annexure Ref"] = row.get("Annexure Ref", "")
    df = pd.DataFrame(rows, columns=["Branch Code", "Branch Name", "Loan Type Code", "Loan Type Name", "A/c No.", "Name", "NPA Code", "Limit Amount (INR)", "Remarks", "Annexure Ref"])
    df.attrs["report_date"] = report_date
    return df

# ─────────────────────────────────────────────────────────────────────────────
# 3. OVERDUE REPORT (exact copy from panchot_report_extractor.py)
# ─────────────────────────────────────────────────────────────────────────────
_DATE_PAT = re.compile(r"^\d{2}/\d{2}/\d{4}$")
_FLOAT_PAT = re.compile(r"^-?[\d,]+\.?\d*$")
_INT_PAT = re.compile(r"^\d+$")
_CONTACT_PAT = re.compile(r"^\d{9,10}$")

def extract_overdue_report(pdf_path):
    report_date = ""
    acct_rows = []
    summary_rows = []
    loan_type_code = loan_type_name = ""

    with pdfplumber.open(pdf_path) as pdf:
        p1_char_rows = _page_rows(pdf.pages[0])

    _SUMMARY_PAT = re.compile(r"^(Typewise|Branchwise|Grand)", re.IGNORECASE)
    blocks = []
    current_block = []

    for top, tokens in p1_char_rows:
        line = _token_text(tokens)
        if not line.strip():
            continue
        m = re.search(r"As On\s+(\d{2}/\d{2}/\d{4})", line, re.IGNORECASE)
        if m and not report_date:
            report_date = m.group(1)
            continue
        if _is_noise(line):
            continue
        m = re.match(r"^\((\d+\s*)\)\s*-\s*(.+)$", line)
        if m:
            code, name = m.group(1).strip(), m.group(2).strip()
            if code != "004":
                loan_type_code, loan_type_name = code, name
            continue
        first_tok = tokens[0][2] if tokens else ""
        is_new_acct = re.match(r"^\d{6}$", first_tok)
        is_summary = _SUMMARY_PAT.match(first_tok)
        if is_new_acct or is_summary:
            if current_block:
                blocks.append(current_block)
            current_block = [(loan_type_code, loan_type_name, top, tokens)]
        else:
            if current_block:
                current_block.append((loan_type_code, loan_type_name, top, tokens))
    if current_block:
        blocks.append(current_block)

    for block in blocks:
        if not block:
            continue
        ltc, ltn, _, primary_tokens = block[0]
        primary_tok_texts = [(t[0], t[2]) for t in primary_tokens]
        first_tok = primary_tokens[0][2] if primary_tokens else ""

        if _SUMMARY_PAT.match(first_tok):
            line = _token_text(primary_tokens)
            nums = [v for _, v in primary_tok_texts if _FLOAT_PAT.match(v)]
            ints = [v for _, v in primary_tok_texts if _INT_PAT.match(v) and v not in nums]
            label = re.match(r"^([\w\s]+Total)", line, re.IGNORECASE)
            summary_rows.append({
                "Loan Type Code": "", "Loan Type Name": "",
                "A/c No.": label.group(1).strip() if label else "Total",
                "Name": f"({ints[0]} accounts)" if ints else "",
                "NPA Code": "", "Category": "",
                "Sanctioned Amt (INR)": nums[0] if len(nums) > 0 else "",
                "Op. Date": "", "Due Date": "", "Int. Rate (%)": "",
                "Adv. Recovery (INR)": nums[1] if len(nums) > 1 else "",
                "Installment Amt (INR)": nums[2] if len(nums) > 2 else "",
                "Outstanding (INR)": nums[3] if len(nums) > 3 else "",
                "Overdue Amt (INR)": nums[4] if len(nums) > 4 else "",
                "Pending Inst.": "", "Overdue Period": "",
                "IR Balance (INR)": nums[5] if len(nums) > 5 else "",
                "Security Amt (INR)": "", "Contact No.": "", "Customer Id": "",
                "Remarks": "SUMMARY",
            })
            continue

        # Account block
        acct_tok = first_tok
        dates = [(x, v) for x, v in primary_tok_texts if _DATE_PAT.match(v)]
        op_date = dates[0][1] if len(dates) > 0 else ""
        due_date = dates[1][1] if len(dates) > 1 else ""

        large_floats = [(x, v) for x, v in primary_tok_texts if _FLOAT_PAT.match(v) and x > 250 and "." in v]
        sanctioned = large_floats[0][1] if large_floats else ""
        neg_floats = [(x, v) for x, v in large_floats if v.startswith("-")]
        outstanding = neg_floats[0][1] if neg_floats else ""
        pos_after_neg = [(x, v) for x, v in large_floats if not v.startswith("-") and x > (neg_floats[0][0] if neg_floats else 0)]
        overdue_amt = pos_after_neg[0][1] if pos_after_neg else ""

        rates = [(x, v) for x, v in primary_tok_texts if _FLOAT_PAT.match(v) and "." in v and 480 < x < 570 and float(v) < 25]
        int_rate = rates[0][1] if rates else ""

        small_ints = [(x, v) for x, v in primary_tok_texts if _INT_PAT.match(v) and x > 720]
        pending_inst = small_ints[0][1] if len(small_ints) > 0 else ""
        overdue_period = small_ints[1][1] if len(small_ints) > 1 else ""

        first_num_x = large_floats[0][0] if large_floats else 999
        name_toks = [v for x, v in primary_tok_texts if x > 60 and x < first_num_x and not _DATE_PAT.match(v) and not _FLOAT_PAT.match(v)]
        name = " ".join(name_toks)

        # Secondary rows
        sec_tokens_all = []
        for _, _, _, sec_toks in block[1:]:
            sec_tokens_all.extend(sec_toks)

        npa_code = next((t[2] for t in sec_tokens_all if _NPA_CODES.match(t[2])), "")
        contact = next((t[2] for t in sec_tokens_all if _CONTACT_PAT.match(t[2])), "")
        floats_sec = [t[2] for t in sec_tokens_all if _FLOAT_PAT.match(t[2]) and t[2] not in (npa_code, contact)]
        cat_toks = [t[2] for t in sec_tokens_all if t[2] not in (npa_code, contact) and not _FLOAT_PAT.match(t[2]) and not _INT_PAT.match(t[2]) and not _CONTACT_PAT.match(t[2])]

        acct_rows.append({
            "Loan Type Code": ltc, "Loan Type Name": ltn,
            "A/c No.": acct_tok, "Name": name,
            "NPA Code": npa_code, "Category": " ".join(cat_toks),
            "Sanctioned Amt (INR)": sanctioned,
            "Op. Date": op_date, "Due Date": due_date,
            "Int. Rate (%)": int_rate,
            "Outstanding (INR)": outstanding, "Overdue Amt (INR)": overdue_amt,
            "Pending Inst.": pending_inst, "Overdue Period": overdue_period,
            "Adv. Recovery (INR)": floats_sec[0] if len(floats_sec) > 0 else "",
            "Installment Amt (INR)": floats_sec[1] if len(floats_sec) > 1 else "",
            "IR Balance (INR)": "", "Security Amt (INR)": "",
            "Contact No.": contact, "Customer Id": "", "Remarks": "",
        })

    # Page 2 processing
    p2_entries = []
    with pdfplumber.open(pdf_path) as pdf:
        if len(pdf.pages) >= 2:
            p2_char_rows = _page_rows(pdf.pages[1])
        else:
            p2_char_rows = []

    skip_headers = {"IR", "Balance", "Security", "Amount", "Contact", "No.", "Customer", "Id"}
    p2_pair = {}
    for _, tokens in p2_char_rows:
        toks = [t[2] for t in tokens if t[2] not in skip_headers]
        if not toks:
            continue
        contacts = [t for t in toks if _CONTACT_PAT.match(t)]
        cust_ids = [t for t in toks if re.match(r"^\d{5,7}$", t) and t not in contacts]
        if contacts or cust_ids:
            p2_pair["contact_p2"] = contacts[0] if contacts else ""
            p2_pair["customer_id"] = cust_ids[0] if cust_ids else ""
            p2_entries.append(dict(p2_pair))
            p2_pair = {}
            continue
        floats = [t for t in toks if _FLOAT_PAT.match(t)]
        if floats:
            real_floats = []
            for f in floats:
                if f.count(".") == 2:
                    m = re.match(r"^(-?[\d]+\.[\d]+)([\d]+\.[\d]+)$", f)
                    if m:
                        real_floats.extend([m.group(1), m.group(2)])
                        continue
                real_floats.append(f)
            p2_pair["ir_balance"] = real_floats[0] if len(real_floats) > 0 else ""
            p2_pair["security_amt"] = real_floats[1] if len(real_floats) > 1 else ""
            if len(real_floats) == 1 and not any(_CONTACT_PAT.match(t) for t in toks):
                p2_entries.append(dict(p2_pair))
                p2_pair = {}

    for i, row in enumerate(acct_rows):
        if i < len(p2_entries):
            e = p2_entries[i]
            row["IR Balance (INR)"] = e.get("ir_balance", "")
            row["Security Amt (INR)"] = e.get("security_amt", "")
            row["Customer Id"] = e.get("customer_id", "")
            if not row["Contact No."]:
                row["Contact No."] = e.get("contact_p2", "")

    all_rows = acct_rows + summary_rows
    columns = [
        "Loan Type Code", "Loan Type Name", "A/c No.", "Name", "NPA Code", "Category",
        "Sanctioned Amt (INR)", "Op. Date", "Due Date", "Int. Rate (%)",
        "Outstanding (INR)", "Overdue Amt (INR)", "Pending Inst.", "Overdue Period",
        "Adv. Recovery (INR)", "Installment Amt (INR)",
        "IR Balance (INR)", "Security Amt (INR)", "Contact No.", "Customer Id", "Remarks", "Annexure Ref"
    ]
    for row in all_rows:
        row["Annexure Ref"] = row.get("Annexure Ref", "")
    df = pd.DataFrame(all_rows, columns=columns)
    df.attrs["report_date"] = report_date
    return df

# ─────────────────────────────────────────────────────────────────────────────
# NPA ACCOUNTS EXTRACTION (alias to overdue report for consistency)
# ─────────────────────────────────────────────────────────────────────────────
def extract_npa_accounts(pdf_path):
    """NPA accounts extraction - uses same parsing as overdue report."""
    return extract_overdue_report(pdf_path)

# ─────────────────────────────────────────────────────────────────────────────
# RECOVERY ACCOUNTS EXTRACTION
# ─────────────────────────────────────────────────────────────────────────────
def extract_recovery_accounts(pdf_path):
    """Recovery accounts extraction using generic table extraction."""
    return extract_pdf_data(pdf_path, "Recovery Accounts")

# ─────────────────────────────────────────────────────────────────────────────
# DISPATCHER (improved to catch "over due", "npa", etc.)
# ─────────────────────────────────────────────────────────────────────────────
def extract_pdf_data(file_path, report_type):
    """Universal PDF extraction with multiple fallback strategies."""
    clean_name = report_type.lower()
    
    # Strategy 1: Specific extractors for known report types
    if "insurance" in clean_name:
        return extract_insurance_pending(file_path)
    elif "cash" in clean_name:
        return extract_cash_summary(file_path)
    elif re.search(r'over\s*due|overdue|loan\s*overdue', clean_name):
        return extract_overdue_report(file_path)
    elif re.search(r'npa|npa\s*accounts', clean_name):
        return extract_overdue_report(file_path)
    elif "recovery" in clean_name:
        return extract_recovery_accounts(file_path)
    
    # Strategy 2: Try table extraction with pdfplumber (best for structured data)
    try:
        with pdfplumber.open(file_path) as pdf:
            all_tables = []
            for page in pdf.pages:
                tables = page.extract_tables()
                for table in tables:
                    if table and len(table) > 1:
                        cleaned_table = []
                        for row in table:
                            cleaned_row = []
                            for cell in row:
                                cleaned_cell = str(cell).strip() if cell else ""
                                cleaned_row.append(cleaned_cell)
                            cleaned_table.append(cleaned_row)
                        
                        df = pd.DataFrame(cleaned_table[1:], columns=cleaned_table[0])
                        df.columns = [str(c).replace('\n', ' ').strip() if c else f"Col_{i}" for i, c in enumerate(df.columns)]
                        all_tables.append(df)
            
            if all_tables:
                final_df = pd.concat(all_tables, ignore_index=True).dropna(how='all')
            else:
                final_df = pd.DataFrame()
    except Exception:
        final_df = pd.DataFrame()
    
    # Strategy 3: Char-level extraction with column detection
    if final_df.empty or len(final_df.columns) < 2:
        try:
            all_rows = _all_rows_multipage(file_path)
            rows = []
            for _, _, tokens in all_rows:
                if len(tokens) >= 2:
                    row = {}
                    for i, t in enumerate(tokens):
                        row[f"Col_{i}"] = t[2]
                    rows.append(row)
            if rows:
                # Try to detect header row
                final_df = pd.DataFrame(rows)
                # Auto-detect header by looking for consistent patterns
                if len(final_df) > 2:
                    first_row = final_df.iloc[0]
                    non_empty_cols = sum(1 for v in first_row if str(v).strip())
                    if non_empty_cols > len(first_row) * 0.5:
                        final_df.columns = [f"Col_{i}" for i in range(len(final_df.columns))]
        except Exception:
            pass
    
    # Strategy 4: OCR fallback for scanned PDFs
    if final_df.empty or len(final_df.columns) < 2:
        try:
            pages = convert_from_path(file_path, dpi=200)
            ocr_rows = []
            for i, page in enumerate(pages):
                text = pytesseract.image_to_string(page)
                lines = [l.strip() for l in text.split('\n') if l.strip()]
                ocr_rows.append({"Page": i+1, "Content": "\n".join(lines)})
            if ocr_rows:
                final_df = pd.DataFrame(ocr_rows)
        except Exception:
            pass
    
    # Ensure Remarks and Annexure Ref columns exist
    if not final_df.empty:
        if 'Remarks' not in final_df.columns:
            final_df['Remarks'] = ""
        if 'Annexure Ref' not in final_df.columns:
            final_df['Annexure Ref'] = ""
    else:
        final_df = pd.DataFrame(columns=['Remarks', 'Annexure Ref'])
    
    return final_df

def process_all_pdfs(upload_dir, file_mappings):
    results = {}
    for sheet_name, filename in file_mappings.items():
        file_path = os.path.join(upload_dir, filename)
        if os.path.exists(file_path):
            results[sheet_name] = extract_pdf_data(file_path, sheet_name)
    return results