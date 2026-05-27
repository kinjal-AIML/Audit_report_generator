import re
import pandas as pd
from typing import List, Dict, Optional


def _find_col(df: pd.DataFrame, candidates: List[str]) -> Optional[str]:
    cols = {str(c).strip(): c for c in df.columns}
    lower_map = {k.lower(): v for k, v in cols.items()}
    for cand in candidates:
        key = cand.lower()
        for col_l, orig in lower_map.items():
            if key == col_l:
                return orig
        # substring fallback
        for col_l, orig in lower_map.items():
            if key in col_l:
                return orig
    return None


def _to_float(val) -> float:
    if val is None:
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val).strip()
    if not s or s.lower() in ("nan", "none"):
        return 0.0
    # keep minus sign, drop commas and other chars except dot
    s = re.sub(r"[^0-9\.-]", "", s)
    try:
        return float(s) if s not in ("", ".", "-") else 0.0
    except Exception:
        return 0.0


def _lakhs(amount: float) -> float:
    return round(amount / 100000.0, 2)


def build_overdue_annexure_summary(df: pd.DataFrame) -> List[Dict[str, str]]:
    """
    Build Annexure-2 style summary from an Overdue sheet/dataframe.
    Detects "loan type" column (e.g., Nature of Facility / Loan Type Name),
    groups by it and computes metrics in lakhs.

    Returns list of rows: {
        sr_no, nature, count, overdue_amt, outstanding, ir_balance
    }
    Note: 'outstanding' may be empty if column not found.
    """
    if df is None or df.empty:
        return []

    # Column detection
    loan_type_col = _find_col(df, [
        "Nature of Facility", "Nature Of Facility", "Facility",
        "Loan Type Name", "Loan Type", "Nature", "Type"
    ])
    # Be explicit about typical column captions found in user sheets
    overdue_col = _find_col(df, [
        "Total Overdue", "Total Overdue Amount", "Overdue Amt (INR)",
        "Overdue Amount (INR)", "Overdue Amount", "Overdue Amt", "Overdue"
    ])
    ir_col = _find_col(df, [
        "IR Balance (INR)", "IR Balance", "Interest Receivable", "IR Amt", "IR Amount"
    ])
    outstanding_col = _find_col(df, [
        "Bal O/s at end month", "Bal O/s", "Balance O/s", "Balance Outstanding",
        "Outstanding (INR)", "Outstanding Amount", "Outstanding"
    ])

    # Fallback: if no explicit loan type, try 'Loan Type Code/Name' pair
    if not loan_type_col:
        code_col = _find_col(df, ["Loan Type Code", "Type Code"])
        name_col = _find_col(df, ["Loan Type Name", "Type Name", "Facility Name"])
        if name_col:
            loan_type_col = name_col
        elif code_col:
            loan_type_col = code_col

    if not loan_type_col:
        # Cannot compute without a grouping key
        return []

    # Clean & filter
    num_cols = [c for c in [overdue_col, ir_col, outstanding_col] if c]
    df_clean = df.copy()
    # Drop pre-existing summary rows like 'Total'
    if loan_type_col in df_clean.columns:
        mask_total = df_clean[loan_type_col].astype(str).str.strip().str.lower() == 'total'
        df_clean = df_clean.loc[~mask_total]
    for c in num_cols:
        df_clean[c] = df_clean[c].map(_to_float).abs()

    # Group and aggregate
    groups = (
        df_clean
        .groupby(loan_type_col, dropna=False)
        .agg(
            account_count=(loan_type_col, "size"),
            overdue_total=(overdue_col, "sum") if overdue_col else (loan_type_col, "size"),
            ir_total=(ir_col, "sum") if ir_col else (loan_type_col, "size"),
            outstanding_total=(outstanding_col, "sum") if outstanding_col else (loan_type_col, "size"),
        )
        .reset_index()
    )

    result: List[Dict[str, str]] = []
    total_count = 0
    total_overdue = 0.0
    total_outstanding = 0.0
    rows_tmp: List[Dict[str, str]] = []
    for idx, row in groups.iterrows():
        nature = str(row.get(loan_type_col, "")).strip()
        if not nature:
            # Skip blank nature groups entirely as requested
            continue
        count = int(row.get("account_count", 0) or 0)
        overdue_sum = float(row.get("overdue_total", 0.0) or 0.0)
        ir_sum = float(row.get("ir_total", 0.0) or 0.0)
        outstanding_sum = float(row.get("outstanding_total", 0.0) or 0.0)

        row_dict = {
            "sr_no": 0,  # temporary; will renumber after sorting
            "nature": nature,
            "count": f"{count:02d}",
            "overdue_amt": f"{_lakhs(overdue_sum):.2f}",
            "outstanding": f"{_lakhs(outstanding_sum):.2f}" if outstanding_col else "",
            "ir_balance": f"{_lakhs(ir_sum):.2f}" if ir_col else "",
        }
        # Provide alias keys commonly expected in templates
        row_dict["total_overdue"] = row_dict["overdue_amt"]
        row_dict["bal_os"] = row_dict["outstanding"]
        rows_tmp.append((count, row_dict, overdue_sum, outstanding_sum))
        total_count += count
        total_overdue += overdue_sum
        total_outstanding += outstanding_sum

    # Sort by account count desc, then by nature asc to stabilize
    rows_tmp.sort(key=lambda t: (-t[0], t[1]["nature"]))
    # Assign Sr No after sorting
    for i, (_, row_dict, _, _) in enumerate(rows_tmp, start=1):
        row_dict["sr_no"] = i
        result.append(row_dict)

    # Append TOTAL row like the requested format
    if result:
        total_row = {
            "sr_no": "TOTAL",
            "nature": "",
            "count": "",
            "overdue_amt": f"{_lakhs(total_overdue):.2f}",
            "outstanding": f"{_lakhs(total_outstanding):.2f}" if outstanding_col else "",
            "ir_balance": f"{_lakhs(groups['ir_total'].sum() if 'ir_total' in groups else 0.0):.2f}" if ir_col else "",
        }
        total_row["total_overdue"] = total_row["overdue_amt"]
        total_row["bal_os"] = total_row["outstanding"]
        result.append(total_row)

    return result
