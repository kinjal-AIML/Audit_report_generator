# AI Concurrent Audit Intelligence Platform 🏦

A production-grade, end-to-end automation platform designed for cooperative banks. The system leverages state-of-the-art AI, OCR, Layout Intelligence, and structured data extraction to automate concurrent audit data preparation, observation drafting, and standardized report generation—all **without using a database**.

---

## 🎯 Project Objective
The platform reduces manual audit work by up to 90% and standardizes reporting through:
- **Databaseless Architecture**: Operates entirely in-memory, using filesystem storage, JSON Mapping, and Excel as the Master Control Panel.
- **Advanced Automated Extraction**: Multi-source ingestion capturing tables, unstructured text, and multi-line semantic records spanning PDFs, Scans, and DOCX files.
- **Relational Integrity**: Links Annexures, Observations, and Accounts seamlessly without SQL.
- **Audit Intelligence**: AI-assisted drafting of observations and semantic anomaly reporting.
- **Report Standardization**: Dynamic population of master Word templates while preserving strict banking layouts.

---

## 🚀 Core 17-Module System Architecture

The platform has been strictly modularized into 17 high-performance engines:

### Extraction & Re-construction Engines (Modules 1-8)
1. **PDF Intelligence Engine**: Detects digital vs scanned PDFs and preserves coordinates.
2. **OCR Engine**: Utilizes `PaddleOCR` to salvage data from degraded or scanned bank documents.
3. **Character-Level Word Reconstruction Engine**: Fixes core banking ERP issues like micro-gap kerning and disjointed characters dynamically.
4. **Document Layout Intelligence**: Analyzes PDF streams to identify bounding boxes for sections and tables using `LayoutParser`.
5. **Semantic Row Reconstruction Engine**: Groups fragmented visual rows spanning multiple horizontal ticks into one logical financial record.
6. **Table Structure Recognition Engine**: Identifies rows, columns, and merged cells globally.
7. **Coordinate Graph Mapping Engine**: Maintains a comprehensive geometric graph of every extracted block.
8. **Template-Aware Extraction Engine**: Applies strictly defined banking heuristics on top of coordinate graphs for deterministic Overdue/Insurance extractions.

### Storage & Relational Mapping Engines (Modules 9-10)
9. **Excel Reconstruction Engine**: Generates `MASTER_AUDIT_DATA.xlsx`, containing universally appended relational keys: `Remarks`, `Annexure Ref`, `Observation ID`.
10. **JSON Mapping Engine**: Resolves the lack of a database by dynamically associating observation IDs to specific anomaly sets across JSON files.

### Automation & Generation Engines (Modules 11-15)
11. **AI Observation Engine**: Converts numerical and mapped anomalies into natural language legal observations without hallucinating financial figures.
12. **Word Template Automation Engine**: Safely binds context variables into the DOCX placeholders.
13. **Annexure Auto-Generation**: Prepares explicit audit annexures mapping to observations.
14. **Date Intelligence Engine**: Controls strict temporal formatting and shift sequences across documents automatically.
15. **DOCX/PDF Export Engine**: Converts final Word docs to secure, locked PDF files.

### Validation & Error Recovery Engines (Modules 16-17)
16. **Validation Engine**: Performs cross-checks, checksums totals, and sweeps for duplicated account entities.
17. **Error Recovery Engine**: Dispatches failover logic—when standard PyMuPDF layout fails on an ERP scan, PaddleOCR immediately spins up.

---

## 📂 Directory Structure
```text
d:/audit_report_generator/
├── main.py               # Main FastAPI Orchestration Entry Point
├── extractors/           # Modules 1-8: Extraction and Reconstruction
│   ├── pdf_intelligence.py
│   ├── ocr_engine.py
│   ├── char_reconstruction_engine.py
│   ├── semantic_row_engine.py
│   ├── layout_engine.py
│   └── coordinate_mapper.py
├── generators/           # Modules 9-13: Storage, AI, Generators
│   ├── excel_reconstruction.py
│   ├── json_mapping_engine.py
│   ├── ai_observation_engine.py
│   └── word_template_engine.py
├── utils/                # Modules 14, 16, 17: Date, Recovery, Validation
│   ├── date_intelligence.py
│   ├── validation_recovery.py
│   └── logger.py
├── templates/            # DOCX Master Templates & HTML views
├── uploads/              # Dynamic Filesystem ingestion
├── extracted/            # JSON Maps and Excel Control panels
├── exports/              # Final DOCX and PDFs
└── requirements.txt      # Production dependencies
```

---

## ⚙️ Installation & Usage

### 1. Requirements
Install the required packages. Ensure you have Python 3.10+ installed.
```powershell
pip install -r requirements.txt
```
*Note: Depending on the OS, PaddleOCR and LayoutParser may require C++ build tools and Poppler.*

### 2. Run the Platform
This project uses `FastAPI` and `uvicorn`.
```powershell
uvicorn main:app --reload --port 5000
```
Open `http://localhost:5000` in your browser.

### 3. Workflow
1. Upload your templates and underlying PDF data.
2. Review the structured output locally in `MASTER_AUDIT_DATA.xlsx` or via the JSON mappings output to `extracted/json/`.
3. Add remarks directly into the system, and endpoints will orchestrate DOCX template substitutions securely.

---

## 🛡️ Data Preservation Rules
The system **ONLY** replaces dynamic placeholders ensuring zero disruption to official banking structures. It strictly preserves:
- Headers & Footers
- Fonts & Spacing
- Tables & Margins
- Page Layouts & Numbering

---

## 📧 Support
For technical issues or custom template integration, contact the System Administrator.
