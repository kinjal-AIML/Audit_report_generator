import pdfplumber
import pandas as pd
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows
import re

# ----------------------------------------------------------------------
# 1. Extract Cash Summary (PANCHOT BR CASH FEB SUM.pdf)
# ----------------------------------------------------------------------
def extract_cash_summary(pdf_path):
    data = {}
    denomination = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue
            # Extract balance figures using regex
            opening = re.search(r"Opening Cash Balance\s*([\d,]+\.?\d*)", text)
            if opening:
                data['Opening Cash Balance'] = float(opening.group(1).replace(',', ''))
            receipt = re.search(r"Total Cash Receipt\s*([\d,]+\.?\d*)", text)
            if receipt:
                data['Total Cash Receipt'] = float(receipt.group(1).replace(',', ''))
            payment = re.search(r"Total Cash Payment\s*([\d,]+\.?\d*)", text)
            if payment:
                data['Total Cash Payment'] = float(payment.group(1).replace(',', ''))
            closing = re.search(r"Closing Cash Balance\s*([\d,]+\.?\d*)", text)
            if closing:
                data['Closing Cash Balance'] = float(closing.group(1).replace(',', ''))

            # Extract denomination table
            denom_lines = re.findall(r"(\d+)\s+NOTE\s+([\d,]+\.?\d*)", text)
            for denom in denom_lines:
                denomination.append({
                    'Denomination': f"{denom[0]} NOTE",
                    'Amount': float(denom[1].replace(',', ''))
                })
            # Also capture 2 RUPEECOIN, 1 RUPEECOIN, 50 PAISA if present
            coin_patterns = [
                (r"2\s+RUPEECOIN\s+([\d,]+\.?\d*)", "2 RUPEECOIN"),
                (r"1\s+RUPEECOIN\s+([\d,]+\.?\d*)", "1 RUPEECOIN"),
                (r"50\s+PAISA\s+([\d,]+\.?\d*)", "50 PAISA")
            ]
            for pattern, name in coin_patterns:
                m = re.search(pattern, text)
                if m:
                    denomination.append({
                        'Denomination': name,
                        'Amount': float(m.group(1).replace(',', ''))
                    })

            # Words in text
            words_match = re.search(r"(Ten Lakh[^\n]*)", text)
            if words_match:
                data['Amount in Words'] = words_match.group(1).strip()
            limit_match = re.search(r"Branch Cash Retention Limit\s*:\s*([\d,]+\.?\d*)", text)
            if limit_match:
                data['Branch Cash Retention Limit'] = float(limit_match.group(1).replace(',', ''))

    return data, denomination

# ----------------------------------------------------------------------
# 2. Extract Overdue Report (PANCHOT BR JAN 2026 OVER DUE REPORT.pdf)
# ----------------------------------------------------------------------
def extract_overdue_report(pdf_path):
    rows = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            # Try table extraction
            table = page.extract_table()
            if table:
                # Identify header row (contains "A/c No", "Account Name", ...)
                header = None
                for i, row in enumerate(table):
                    if row and any('A/c No' in str(cell) for cell in row):
                        header = [str(cell).strip() if cell else '' for cell in row]
                        # Start data rows after header
                        for r in table[i+1:]:
                            if r and any(cell and cell.strip() for cell in r):
                                rows.append([str(cell).strip() if cell else '' for cell in r])
                        break
                # If no header found, assume first row is header
                if not header and table:
                    header = [str(cell).strip() if cell else '' for cell in table[0]]
                    for row in table[1:]:
                        if row and any(cell and cell.strip() for cell in row):
                            rows.append([str(cell).strip() if cell else '' for cell in row])
            else:
                # Fallback: extract text line by line
                text = page.extract_text()
                if text:
                    lines = text.split('\n')
                    # Find line with column headers
                    for i, line in enumerate(lines):
                        if 'A/c No' in line and 'Account Name' in line:
                            header = line.split()
                            # Subsequent lines are data until empty line or totals
                            for ln in lines[i+1:]:
                                if ln.strip() and not ln.startswith('Typewise'):
                                    # crude split by spaces, better to use fixed widths?
                                    # For simplicity, we'll skip and rely on table extraction
                                    pass
                            break
    # Convert to DataFrame
    if rows:
        # Ensure all rows have same length as header
        max_cols = max(len(row) for row in rows)
        header_len = len(header) if header else max_cols
        for row in rows:
            while len(row) < header_len:
                row.append('')
        df = pd.DataFrame(rows, columns=header if header else [f'Col_{i}' for i in range(header_len)])
        # Remove rows that are all empty or contain only totals
        df = df[~df.iloc[:, 0].astype(str).str.contains('Typewise|Branchwise|Grand Total', na=False)]
        return df
    else:
        return pd.DataFrame()

# ----------------------------------------------------------------------
# 3. Extract Insurance Pending Registration (PANCHOT BR JAN 2026 INSURANCE PENDING REGI..pdf)
# ----------------------------------------------------------------------
def extract_insurance_pending(pdf_path):
    # This PDF seems to contain a list of numbers (possibly serial numbers or pending IDs)
    # Extract all numeric tokens and maintain order.
    numbers = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                # Find all sequences of digits (including decimals if needed)
                tokens = re.findall(r'\b\d+(?:\.\d+)?\b', text)
                numbers.extend(tokens)
    # Convert to DataFrame with a single column
    df = pd.DataFrame(numbers, columns=['Pending Registration No. / ID'])
    return df

# ----------------------------------------------------------------------
# Main: write all extracted data to an Excel file with multiple sheets
# ----------------------------------------------------------------------
def main():
    # Paths to the PDF files (adjust as needed)
    cash_pdf = "D:\\audit_report_generator\\uploads\\PANCHOT BR CASH FEB SUM.pdf"
    overdue_pdf = "D:\\audit_report_generator\\uploads\\PANCHOT BR JAN 2026 OVER DUE REPORT.pdf"
    insurance_pdf = "D:\\audit_report_generator\\uploads\\PANCHOT BR JAN 2026 INSURANCE PENDING REGI.pdf"

    # Extract data
    cash_data, denom_data = extract_cash_summary(cash_pdf)
    overdue_df = extract_overdue_report(overdue_pdf)
    insurance_df = extract_insurance_pending(insurance_pdf)

    # Create Excel writer
    output_file = "extracted_data.xlsx"
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        # Sheet 1: Cash Summary (key-value pairs)
        if cash_data:
            cash_df = pd.DataFrame(list(cash_data.items()), columns=['Item', 'Amount (INR)'])
            cash_df.to_excel(writer, sheet_name='Cash Summary', index=False)
        else:
            pd.DataFrame({'Message': ['No cash summary data found']}).to_excel(writer, sheet_name='Cash Summary', index=False)

        # Sheet 2: Denomination breakdown
        if denom_data:
            denom_df = pd.DataFrame(denom_data)
            denom_df.to_excel(writer, sheet_name='Denomination', index=False)
        else:
            pd.DataFrame({'Message': ['No denomination data found']}).to_excel(writer, sheet_name='Denomination', index=False)

        # Sheet 3: Overdue Report
        if not overdue_df.empty:
            overdue_df.to_excel(writer, sheet_name='Overdue Report', index=False)
        else:
            pd.DataFrame({'Message': ['No overdue data found']}).to_excel(writer, sheet_name='Overdue Report', index=False)

        # Sheet 4: Insurance Pending Registration
        if not insurance_df.empty:
            insurance_df.to_excel(writer, sheet_name='Insurance Pending', index=False)
        else:
            pd.DataFrame({'Message': ['No insurance pending data found']}).to_excel(writer, sheet_name='Insurance Pending', index=False)

    print(f"Data successfully extracted to {output_file}")

if __name__ == "__main__":
    main()