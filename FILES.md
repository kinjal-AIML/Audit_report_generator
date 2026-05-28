# Project Flow and File Guide

This document explains how the app runs, which files are involved in the runtime flow, and which files appear unused (safe to archive/delete if you don’t rely on them). Links below are workspace-relative.

---

## How It Runs

- Web server: [app.py](app.py) (Flask)
- Frontend UI: [templates/index.html](templates/index.html)
- Report templates: [templates/UPDATED_MNSB_TEMPLATE_DYNAMIC.docx](templates/UPDATED_MNSB_TEMPLATE_DYNAMIC.docx) (used for dynamic MNSB); may also use [templates/UPDATED_MNSB_TEMPLATE.docx](templates/UPDATED_MNSB_TEMPLATE.docx) and [templates/UPDATED_CNSB_TEMPLATE.docx](templates/UPDATED_CNSB_TEMPLATE.docx) depending on upload.
- DOCX rendering: [generators/report_generator.py](generators/report_generator.py) using `docxtpl`
- Template parsing (questions/sections): [utils/template_parser.py](utils/template_parser.py)
- PDF/Excel processing: [extractors/pdf_extractor.py](extractors/pdf_extractor.py), [utils/excel_generator.py](utils/excel_generator.py), [utils/docx_to_excel.py](utils/docx_to_excel.py)
- Date/number helpers and annexures: [utils/date_utils.py](utils/date_utils.py), [utils/number_to_words.py](utils/number_to_words.py), [utils/annexure_utils.py](utils/annexure_utils.py)

### High-Level Request Flow
1. Parse Template (Step 1)
   - UI posts to `/parse-template` with a DOCX → server saves as `templates/USER_UPLOADED_TEMPLATE.docx` and parses schema via `parse_docx_template()` → UI renders questions.
2. Extract Data (Step 1)
   - UI posts PDFs to `/extract-data` → processed via `process_all_pdfs()` in [extractors/pdf_extractor.py](extractors/pdf_extractor.py) and mapped to tables → master context built via [utils/date_utils.py](utils/date_utils.py) + placeholders.
3. Review & Edit (Step 2)
   - UI shows master fields, tables for inline edits, and question grid (“Auditor Remark”, “Reply of Branch”, “Annexure Ref”).
4. Finalize (Step 3)
   - UI posts to `/finalize-report` → server merges `answers` into `schema.sections[].questions[]`, computes annexures, and renders DOCX via [generators/report_generator.py](generators/report_generator.py) with [templates/UPDATED_MNSB_TEMPLATE_DYNAMIC.docx](templates/UPDATED_MNSB_TEMPLATE_DYNAMIC.docx).
   - Notes: per-question aliases are provided so both `q.remark` and `q.auditor_comment` resolve; `q.question` and `q.audit_review` also resolve.

### Run Commands (Windows)
```powershell
(Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned) ; (& d:\audit_report_generator\venv\Scripts\Activate.ps1)
python app.py
```
Open http://localhost:5050

---

## Active Runtime Files (Keep)
- Entry point
  - [app.py](app.py)
- Templates (frontend and DOCX)
  - [templates/index.html](templates/index.html)
  - [templates/UPDATED_MNSB_TEMPLATE_DYNAMIC.docx](templates/UPDATED_MNSB_TEMPLATE_DYNAMIC.docx)
  - [templates/USER_UPLOADED_TEMPLATE.docx](templates/USER_UPLOADED_TEMPLATE.docx) (created at runtime when you upload)
  - Optionally: [templates/UPDATED_MNSB_TEMPLATE.docx](templates/UPDATED_MNSB_TEMPLATE.docx), [templates/UPDATED_CNSB_TEMPLATE.docx](templates/UPDATED_CNSB_TEMPLATE.docx)
- Generators
  - [generators/report_generator.py](generators/report_generator.py)
- Extractors
  - [extractors/pdf_extractor.py](extractors/pdf_extractor.py)
  - [extractors/cnsb_extractor.py](extractors/cnsb_extractor.py)
  - [extractors/mnsb_extractor.py](extractors/mnsb_extractor.py)
  - [extractors/docx_table_extractor.py](extractors/docx_table_extractor.py)
- Utils
  - [utils/template_parser.py](utils/template_parser.py)
  - [utils/excel_generator.py](utils/excel_generator.py)
  - [utils/docx_to_excel.py](utils/docx_to_excel.py)
  - [utils/date_utils.py](utils/date_utils.py)
  - [utils/number_to_words.py](utils/number_to_words.py)
  - [utils/annexure_utils.py](utils/annexure_utils.py)
  - [utils/logger.py](utils/logger.py) (imported by several utility engines)
- Static & folders used at runtime
  - [static/](static/) (assets for the UI)
  - [uploads/](uploads/) (ingest area for PDFs/DOCX)
  - [outputs/](outputs/) (generated DOCX/PDF/Excel)
- Environment & dependencies
  - [requirements.txt](requirements.txt)

---

## Potentially Unused/Legacy (Not referenced by main app flow)
These are not imported by [app.py](app.py). If you don’t use their standalone/CLI flows, you can archive or delete.

- Legacy/alternate app
  - [app_old.py](app_old.py)
- One-off scripts
  - [extract_pdfs_to_excel.py](extract_pdfs_to_excel.py)
  - [extract_placeholders.py](extract_placeholders.py)
  - [panchot_report_extractor.py](panchot_report_extractor.py)
  - [panchot_report_extractor_new.py](panchot_report_extractor_new.py)
  - [check_braces.py](check_braces.py)
- AI/engines not in current HTTP flow (no active imports in web path)
  - [ai/ai_remark_generator.py](ai/ai_remark_generator.py)
  - [generators/ai_observation_engine.py](generators/ai_observation_engine.py)
  - [generators/excel_reconstruction.py](generators/excel_reconstruction.py)
  - [generators/json_mapping_engine.py](generators/json_mapping_engine.py)
  - [generators/word_template_engine.py](generators/word_template_engine.py)
  - [extractors/char_reconstruction_engine.py](extractors/char_reconstruction_engine.py)
  - [extractors/coordinate_mapper.py](extractors/coordinate_mapper.py)
  - [extractors/layout_engine.py](extractors/layout_engine.py)
  - [extractors/semantic_row_engine.py](extractors/semantic_row_engine.py)
  - [extractors/pdf_intelligence.py](extractors/pdf_intelligence.py)
  - [extractors/ocr_engine.py](extractors/ocr_engine.py)
- Tests and samples
  - [tests/](tests/) (optional to keep for dev)
  - [test.py](test.py), [test_output.txt](test_output.txt)
  - [demo.txt](demo.txt), [DEMO_WORKFLOW.md](DEMO_WORKFLOW.md)

> Note: Some of the “engines” above could be future helpers for PDF parsing. Today, `app.py` only uses [extractors/pdf_extractor.py](extractors/pdf_extractor.py). If you plan to expand parsing, consider keeping these under `archive/` rather than deleting.

---

## Endpoint Summary (for reference)
- `/` → UI index
- `/parse-template` → Save + parse uploaded DOCX to schema
- `/extract-data` → Ingest PDFs, extract tables, build master context
- `/process-pdfs-now` → On-demand PDF processing
- `/download-excel-now` → Export edited tables to Excel
- `/finalize-report` → Merge answers, prepare annexures, render DOCX/PDF/Excel
- `/load-existing-master-excel` → Load prior MASTER_AUDIT_DATA.xlsx
- `/download/<filename>` → Serve files from outputs

---

## Deletion Checklist
1. Move candidates to an `archive/` folder first.
2. Run the app, exercise all main flows (parse template, extract data, finalize).
3. If nothing breaks and you don’t need the archived scripts, delete them.
