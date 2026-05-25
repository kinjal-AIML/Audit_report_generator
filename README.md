# AI Concurrent Audit Intelligence Platform 🏦

A production-grade, end-to-end automation platform designed for cooperative banks (like CNSB and MNSB). The system leverages AI and structured data extraction to automate concurrent audit data preparation, observation drafting, and standardized report generation.

---

## 🎯 Project Objective
The platform reduces manual audit work by up to 90% and standardizes reporting through:
- **Automated Data Extraction**: Multi-source ingestion from DOCX, PDF, and Excel.
- **Annexure Preparation**: Instant generation of standardized audit annexures.
- **Audit Intelligence**: AI-assisted drafting of observations and NPA summaries.
- **Report Standardization**: Dynamic population of master templates while preserving pixel-perfect formatting.
- **DOCX/PDF Generation**: Seamless conversion of audit reports to ready-to-sign formats.

---

## 🚀 Core System Workflow

### STEP 1 — User Input
Upload the current month's **CNSB/MNSB Master Template** along with supporting PDF reports:
- Insurance Report
- Loan Overdue Report
- Encashment Report
- NPA Report
- Recovery Report
- Stock Statement Report

### STEP 2 — Data Extraction Engine
Extracts structured data using a robust pipeline:
- **Extraction Tools**: `pdfplumber`, `camelot-py`, `tabula-py`, `python-docx`.
- **Key Data Points**: Account numbers, balances, overdue amounts, insurance expiry dates, NPA values, recovery amounts, and audit observations.

### STEP 3 — Structured Master Excel (SOURCE OF TRUTH)
The system generates a `MASTER_AUDIT_DATA.xlsx` which serves as the centralized data store.
**Sheets Included:**
1. **Audit Summary**
2. **Insurance Report**
3. **Loan Overdue**
4. **Encashment Report**
5. **NPA Accounts**
6. **Recovery Accounts**
7. **Audit Observations**
8. **Annexures**

*Note: All sheets include mandatory **Remarks** and **Annexure Reference** columns for audit compliance.*

### STEP 8 — Date Automation
Input a single start date (e.g., `2026-02-01`), and the system automatically generates:
- **Period Start**: `01-02-2026`
- **Period End**: `28-02-2026` (Auto-calculates month-end)
- **Cash Verification Date**: `13-03-2026` (+13 days)
- **Report Date**: `16-03-2026` (+16 days)

### STEP 9 — User Review Panel
A professional interactive dashboard allows auditors to:
- **Edit Extracted Fields**: Fine-tune branch names, balances, and dates.
- **Modify Observations**: Update remarks and annexure references in real-time.
- **Regenerate & Preview**: Instantly update the report structure before final export.

### STEP 10 — Final Outputs
- **MASTER_AUDIT_DATA.xlsx**: The complete audited dataset.
- **CNSB Audit Report (DOCX)**: High-fidelity document preserving all original formatting.
- **Final PDF Report**: Ready-for-signature digital report.
- **Annexure Workbook**: Comprehensive audit annexures in Excel format.

---

## 🛠️ Tech Stack
- **Backend**: Python 3.10+, Flask 3.x
- **Data Engineering**: Pandas, OpenPyXL
- **Document Processing**: `docxtpl`, `python-docx`
- **PDF Extraction**: `pdfplumber`, `camelot-py`
- **Templating Engine**: Jinja2 (Web), DocxTemplate (Word)
- **Frontend**: HTML5, CSS3, jQuery, Bootstrap 4 (AdminLTE 3 Integration)

---

## 📂 Directory Structure
```text
d:/audit_report_generator/
├── app.py                # Main Flask entry point & API orchestration
├── extractors/           # Extraction logic for PDF/DOCX formats
│   ├── cnsb_extractor.py # CNSB template parsing
│   ├── mnsb_extractor.py # MNSB template parsing
│   └── pdf_extractor.py  # Structured table extraction from PDFs
├── generators/           # Document & PDF generation engines
│   └── report_generator.py
├── utils/                # Utility & Automation modules
│   ├── date_utils.py     # Step 8: Automatic date calculation logic
│   ├── excel_generator.py # Step 3/10: Master Excel creation logic
│   └── pdf_converter.py  # DOCX to PDF conversion utility
├── templates/            # DOCX Master Templates & HTML views
│   ├── UPDATED_CNSB_TEMPLATE.docx
│   ├── index.html        # Step 9: User Review Panel & Dashboard
└── requirements.txt      # Production dependencies
```

---

## ⚙️ Installation & Usage

### 1. Requirements
Install the required packages:
```powershell
pip install -r requirements.txt
```

### 2. Run the Platform
```powershell
python app.py
```
Open `http://localhost:5000` in your browser.

### 3. Report Templates
Place your standardized bank templates in the `templates/` folder. Ensure they contain the following placeholders for replacement:
`{{branch_name}}`, `{{period_start}}`, `{{period_end}}`, `{{cash_verification_date}}`, `{{report_date}}`, `{{closing_cash_balance}}`, `{{npa_summary}}`, `{{annexure_reference}}`, `{{audit_observation}}`.

---

## 🛡️ Data Preservation Rules
The system **ONLY** replaces dynamic placeholders. It strictly preserves:
- Headers & Footers
- Fonts & Spacing
- Tables & Margins
- Page Layouts & Numbering

---

## 📧 Support
For technical issues or custom template integration, contact the System Administrator.
