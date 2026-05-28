from flask import Flask, render_template, request, jsonify, send_from_directory, session
from flask_cors import CORS
import os
import shutil
import json
import re
import pandas as pd
import numpy as np
from extractors.cnsb_extractor import extract_cnsb_data
from extractors.mnsb_extractor import extract_mnsb_data
from extractors.pdf_extractor import process_all_pdfs, extract_cash_summary
from extractors.docx_table_extractor import extract_tables_from_docx
from generators.report_generator import generate_report
from utils.date_utils import parse_date, format_date, build_template_context
from utils.excel_generator import generate_master_excel, generate_annexure_workbook
from utils.docx_to_excel import generate_docx_like_excel
from utils.number_to_words import number_to_indian_rupees
from utils.annexure_utils import build_overdue_annexure_summary
from utils.template_parser import parse_docx_template

app = Flask(__name__)
app.secret_key = "supersecretkey" # For session storage
CORS(app)

UPLOAD_DIR = "uploads"
OUTPUT_DIR = "outputs"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

def sanitize_for_json(obj):
    """
    Recursively sanitize objects for JSON serialization,
    handling NumPy types and Pandas NA values.
    """
    if isinstance(obj, dict):
        return {k: sanitize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_for_json(v) for v in obj]
    elif isinstance(obj, (np.integer, np.floating)):
        return obj.item() if not np.isnan(obj) else None
    elif isinstance(obj, np.ndarray):
        return sanitize_for_json(obj.tolist())
    elif pd.isna(obj):
        return None
    return obj

def get_file_mappings(files):
    """Helper to map uploaded files to standard report names."""
    mappings = {}
    for f in files:
        if not f.filename: continue
        name_lower = f.filename.lower()
        if re.search(r'insurance', name_lower):
            mappings["Insurance Pending Register"] = f.filename
        elif re.search(r'cash', name_lower):
            mappings["Cash report"] = f.filename
        elif re.search(r'npa', name_lower):
            mappings["NPA Accounts"] = f.filename
        elif re.search(r'over\s*due|overdue', name_lower):
            mappings["Loan Overdue"] = f.filename
        elif re.search(r'recovery', name_lower):
            mappings["Recovery Accounts"] = f.filename
        elif re.search(r'limit', name_lower):
            mappings["Limit Register"] = f.filename
        elif re.search(r'trial|balance', name_lower):
            mappings["Trial Balance"] = f.filename
        else:
            mappings[os.path.splitext(f.filename)[0]] = f.filename
    return mappings

@app.route('/')
def index():
    return render_template('index.html')
@app.route('/parse-template', methods=['POST'])
def parse_template_route():
    try:
        if 'audit_file' not in request.files:
            return jsonify({"error": "No audit file uploaded"}), 400
        audit_file = request.files['audit_file']
        if not audit_file.filename.lower().endswith('.docx'):
            return jsonify({"error": "Please upload a DOCX file"}), 400

        # Save uploaded template into templates dir for later rendering
        templates_dir = os.path.join('templates')
        os.makedirs(templates_dir, exist_ok=True)
        saved_name = f"USER_UPLOADED_TEMPLATE.docx"
        saved_path = os.path.join(templates_dir, saved_name)
        audit_file.save(saved_path)

        schema = parse_docx_template(saved_path)
        # Keep only lightweight items in session
        session['template_name'] = saved_name
        # Do NOT store schema in session to avoid large cookies
        return jsonify({"message": "Parsed successfully", "schema": schema, "template_name": saved_name})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/save-answers', methods=['POST'])
def save_answers_route():
    """
    Save question answers temporarily in session (for stateless operation,
    the frontend will re-send answers in /finalize-report).
    """
    try:
        answers = request.json.get('answers', {})
        session['answers'] = answers
        return jsonify({"message": "Answers saved"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/extract-data', methods=['POST'])
def extract_data_route():
    try:
        if 'audit_file' not in request.files:
            return jsonify({"error": "No audit file uploaded"}), 400

        pdf_files = request.files.getlist('pdf_files') or []
        audit_file = request.files['audit_file']
        start_date_str = request.form.get('start_date', '2026-02-01')

        if not audit_file.filename.lower().endswith('.docx'):
            return jsonify({"error": "Audit file must be DOCX"}), 400

        # Save audit template
        templates_dir = os.path.join('templates')
        os.makedirs(templates_dir, exist_ok=True)
        audit_path = os.path.join(templates_dir, 'USER_UPLOADED_TEMPLATE.docx')
        audit_file.save(audit_path)

        # Parse template to get questions schema
        schema = parse_docx_template(audit_path)
        session['template_name'] = 'USER_UPLOADED_TEMPLATE.docx'

        # Save PDFs
        saved_pdfs = {}
        for pdf in pdf_files:
            if pdf and pdf.filename.lower().endswith('.pdf'):
                pdf_path = os.path.join(UPLOAD_DIR, pdf.filename)
                pdf.save(pdf_path)
                saved_pdfs[pdf.filename] = pdf_path

        # Initialize master data with placeholders
        master_data = {
            'branch_name': '',
            'branch_code': '',
            'report_date': start_date_str,
            'report_month': 'February 2026',
            'auditor_name': '',
            'auditor_id': '',
            'audit_period': 'FY 2025-26'
        }

        # Initialize tables structure
        tables = {
            'Cash report': [],
            'NPA Accounts': [],
            'Insurance Pending Register': [],
            'Loan Overdue': [],
            'Trial Balance': []
        }

        # Mark schema for later use
        session['schema'] = schema

        # Check if deferring PDFs
        defer_pdfs = request.form.get('defer_pdfs') == '1'
        if not defer_pdfs and saved_pdfs:
            # Immediate processing (slower)
            try:
                processed = process_all_pdfs(saved_pdfs)
                for report_type, records in processed.items():
                    tables[report_type] = sanitize_for_json(records)
            except Exception:
                pass  # PDFs are optional; continue without them

        return jsonify({
            "message": "Data extracted",
            "data": {
                "master_data": master_data,
                "tables": tables
            },
            "schema": schema,
            "files": {}
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/process-pdfs-now', methods=['POST'])
def process_pdfs_now():
    """Process all PDFs in uploads dir and return tables."""
    try:
        pdf_files = {}
        for fname in os.listdir(UPLOAD_DIR):
            if fname.lower().endswith('.pdf'):
                pdf_files[fname] = os.path.join(UPLOAD_DIR, fname)

        tables = {}
        if pdf_files:
            processed = process_all_pdfs(pdf_files)
            tables = {k: sanitize_for_json(v) for k, v in processed.items()}

        return jsonify({"tables": tables})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/extract-excel-docx', methods=['POST'])
def extract_excel_docx():
    """Quick extract: DOCX template → Excel"""
    try:
        if 'audit_file' not in request.files:
            return jsonify({"error": "No DOCX file"}), 400

        audit_file = request.files['audit_file']
        templates_dir = 'templates'
        os.makedirs(templates_dir, exist_ok=True)
        audit_path = os.path.join(templates_dir, 'USER_UPLOADED_TEMPLATE.docx')
        audit_file.save(audit_path)

        excel_path = generate_docx_like_excel(audit_path, OUTPUT_DIR)
        return jsonify({"file": f"/download/{os.path.basename(excel_path)}"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/extract-excel-pdf', methods=['POST'])
def extract_excel_pdf():
    """Quick extract: PDFs → Excel"""
    try:
        pdf_files = {}
        for fname in os.listdir(UPLOAD_DIR):
            if fname.lower().endswith('.pdf'):
                pdf_files[fname] = os.path.join(UPLOAD_DIR, fname)

        if not pdf_files:
            return jsonify({"error": "No PDFs to process"}), 400

        processed = process_all_pdfs(pdf_files)
        excel_path = generate_master_excel(
            {k: pd.DataFrame(v) for k, v in processed.items()},
            OUTPUT_DIR
        )
        return jsonify({"file": f"/download/{os.path.basename(excel_path)}"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/download-excel-now', methods=['POST'])
def download_excel_now():
    """User clicks 'Download Excel Now' to export current edited state"""
    try:
        form_data = request.json
        table_data = form_data.get('table_data', {})
        excel_data = {k: pd.DataFrame(v) for k, v in table_data.items()}
        excel_path = generate_master_excel(excel_data, OUTPUT_DIR)
        return jsonify({"file": f"/download/{os.path.basename(excel_path)}"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# =============================================================================
# CRITICAL: /finalize-report endpoint with CORRECTED MERGE LOGIC
# =============================================================================
@app.route('/finalize-report', methods=['POST'])
def finalize_report_route():
    """
    FIX SUMMARY:
    1. Always overwrite q[field] with merged answer value
    2. Add debug logging to verify merge happened
    3. Add alias fields for template compatibility
    4. Log first 2 questions before render to confirm
    """
    try:
        form_data = request.json
        master_data = form_data.get('master_data')
        table_data = form_data.get('table_data')
        template_name = session.get('template_name', 'UPDATED_CNSB_TEMPLATE.docx')
        
        # CRITICAL: Answers are passed in payload to avoid session size issues
        answers = form_data.get('answers', {})
        
        # Optional parsed schema (sections/questions) from client
        schema = form_data.get('schema') or {}
        
        # === DEBUG LOG 1: Confirm answers received ===
        print("\n" + "="*80)
        print("DEBUG: /finalize-report - ANSWERS RECEIVED FROM FRONTEND")
        print("="*80)
        print(json.dumps(answers, indent=2)[:500])  # First 500 chars
        print(f"Total answer keys: {len(answers)}")
        print("="*80 + "\n")
        
        excel_data = {k: pd.DataFrame(v) for k, v in table_data.items()}
        excel_path = generate_master_excel(excel_data, OUTPUT_DIR)
        annexure_path = generate_annexure_workbook(excel_data, OUTPUT_DIR)
        
        summaries = []
        insurance_list = []
        overdue_summary_list = []
        
        for s_name, records in table_data.items():
            # Special handling for Insurance Pending Register (Annexure -1)
            if "insurance" in s_name.lower():
                def _fmt_ac3(v):
                    s = str(v or "").strip()
                    digits = ''.join(ch for ch in s if ch.isdigit())
                    if not digits:
                        return s
                    # Use last 3 digits, left-pad with zeros
                    tail = digits[-3:]
                    return tail.zfill(3)

                filtered = []
                for r in records:
                    name_val = str(r.get('Name', '') or '').strip()
                    remarks_val = str(r.get('Remarks', '') or '')
                    ac = r.get('A/c No.', r.get('Account No', ''))
                    # Skip totals/summary rows and blank account rows
                    if not ac:
                        continue
                    if re.search(r"total", name_val, re.IGNORECASE):
                        continue
                    if re.search(r"count\s*:\s*\d+", remarks_val, re.IGNORECASE):
                        continue
                    filtered.append(r)

                for idx, r in enumerate(filtered, 1):
                    limit_val = r.get('Limit Amount (INR)', '0')
                    try:
                        clean_limit = str(limit_val).replace(',', '').strip()
                        limit_lacs = float(clean_limit) / 100000.0
                        limit_str = f"{limit_lacs:.2f}"
                    except:
                        limit_str = str(limit_val)

                    ac_display = _fmt_ac3(r.get('A/c No.', r.get('Account No', '')))

                    insurance_list.append({
                        "sr_no": idx,
                        "name": r.get('Name', ''),
                        "nature": r.get('Loan Type Name', ''),
                        "ac_no": ac_display,
                        "limit": limit_str,
                        "reply": r.get('Remarks', '')
                    })
            
            # Special handling for Overdue Summary (Annexure -2)
            if "overdue" in s_name.lower() or "npa" in s_name.lower():
                # Prefer computed summary from the full sheet if available
                try:
                    df_overdue = pd.DataFrame(records)
                    computed = build_overdue_annexure_summary(df_overdue)
                except Exception:
                    computed = []

                if computed:
                    # Keep reply field for templating compatibility
                    for row in computed:
                        row.setdefault("reply", "")
                    overdue_summary_list.extend(computed)
                else:
                    # Fallback to pre-parsed SUMMARY rows (existing behavior)
                    summary_idx = 1
                    for r in records:
                        if str(r.get('Remarks', '')).upper() == 'SUMMARY':
                            nature = r.get('A/c No.', 'Total')
                            count_text = r.get('Name', '(0 accounts)')
                            m = re.search(r'(\d+)', str(count_text))
                            count = m.group(1) if m else "0"
                            overdue_summary_list.append({
                                "sr_no": summary_idx,
                                "nature": nature,
                                "count": count,
                                "overdue_amt": r.get('Overdue Amt (INR)', '0'),
                                "outstanding": r.get('Outstanding (INR)', '0'),
                                "reply": ""
                            })
                            summary_idx += 1

            for r in records:
                rmk, ref = r.get('Remarks', ''), r.get('Annexure Ref', '')
                if rmk or ref:
                    summaries.append(f"{s_name}: {rmk}" + (f" [{ref}]" if ref else ""))
        
        master_data['annexure_summaries'] = "\n".join(summaries)
        master_data['annexure_count'] = len(summaries)
        master_data['insurance_pending'] = insurance_list
        master_data['overdue_summary'] = overdue_summary_list
        # Bind dynamic answers for template placeholders
        master_data['answers'] = answers
        
        # === CRITICAL: Merge schema with answers ===
        if isinstance(schema, dict) and schema.get('sections'):
            sections = schema.get('sections') or []
            
            print("\n" + "="*80)
            print("DEBUG: MERGING ANSWERS INTO SCHEMA")
            print(f"Sections: {len(sections)}")
            for si, sec in enumerate(sections):
                print(f"  Section {si}: {sec.get('section_name')} - {len(sec.get('questions', []))} questions")
            print("="*80 + "\n")
            
            try:
                # answers is expected in shape: { key: { remark, branch_reply, annexure_reference } }
                for sec_idx, sec in enumerate(sections):
                    for q_idx, q in enumerate(sec.get('questions') or []):
                        # Prefer explicit key from parser; else derive a slug from text
                        key = q.get('key') or re.sub(r"[^A-Za-z0-9]+", "_", str(q.get('question') or '').strip()).strip('_').lower()
                        
                        # Get answers for this question
                        a = answers.get(key, {}) if isinstance(answers, dict) else {}
                        
                        # === FIX: ALWAYS update with merged values (not just when non-null) ===
                        # This ensures user edits are preserved
                        if a:
                            q['remark'] = a.get('remark', '')
                            q['branch_reply'] = a.get('branch_reply', '')
                            q['annexure_reference'] = a.get('annexure_reference', '')
                        
                        # === Provide alias fields for template compatibility ===
                        # Map: question -> audit_review, remark -> auditor_comment
                        q['audit_review'] = q.get('question', '')
                        q['auditor_comment'] = q.get('remark', '')
                        q['reply_of_branch'] = q.get('branch_reply', '')
                        
                        # Debug: log first 2 questions from first section
                        if sec_idx == 0 and q_idx < 2:
                            print(f"DEBUG: Question {key}")
                            print(f"  - question: {q.get('question', '')[:60]}")
                            print(f"  - auditor_comment: {q.get('auditor_comment', '')[:60]}")
                            print(f"  - branch_reply: {q.get('branch_reply', '')[:60]}")
                            print(f"  - annexure_reference: {q.get('annexure_reference', '')[:60]}")
                
                print("\n" + "="*80)
                print("DEBUG: MERGE COMPLETE")
                print("="*80 + "\n")
                
            except Exception as e:
                print(f"ERROR during merge: {str(e)}")
                import traceback
                traceback.print_exc()
                # Failsafe – don't block report generation if merging has an issue
                pass
            
            master_data['sections'] = sections
        
        # Dynamic Comments for main audit table
        master_data['comment_insurance'] = "As per Annexure-1" if insurance_list else "Nil"
        master_data['comment_overdue'] = "As per Annexure-2" if overdue_summary_list else "Nil"
        
        # Check if we have any data/remarks for Cash Credit or Bills
        cash_credit_remarks = [r.get('Remarks', '') for s, recs in table_data.items() if "cash credit" in s.lower() for r in recs if r.get('Remarks')]
        bills_remarks = [r.get('Remarks', '') for s, recs in table_data.items() if "bill" in s.lower() for r in recs if r.get('Remarks')]
        
        master_data['comment_cash_credit'] = cash_credit_remarks[0] if cash_credit_remarks else "Branch has not sanctioned any advances against the Stock / book debt hence we have no remarks to offer."
        master_data['comment_bills_register'] = bills_remarks[0] if bills_remarks else "Not applicable, as no such facility is granted by branch."
        master_data['comment_default_nil'] = "Nil"
        
        # Use dynamic template if available
        final_template = template_name
        # Prefer dynamic template when we have parsed sections/questions
        if (isinstance(schema, dict) and schema.get('sections')):
            final_template = "UPDATED_MNSB_TEMPLATE_DYNAMIC.docx"
        elif template_name == "UPDATED_MNSB_TEMPLATE.docx":
            final_template = "UPDATED_MNSB_TEMPLATE_DYNAMIC.docx"
        
        print("\n" + "="*80)
        print(f"DEBUG: RENDERING TEMPLATE: {final_template}")
        print("="*80 + "\n")
        
        output_docx = generate_report(template_name=final_template, context=master_data)
        
        print("\n" + "="*80)
        print(f"DEBUG: DOCX GENERATED: {output_docx}")
        print("="*80 + "\n")
        
        return jsonify({
            "message": "Generated successfully",
            "files": {
                "docx": f"/download/{os.path.basename(output_docx)}",
                "pdf": f"/download/{os.path.basename(output_docx.replace('.docx', '.pdf'))}",
                "excel": f"/download/{os.path.basename(excel_path)}",
                "annexure": f"/download/{os.path.basename(annexure_path)}"
            }
        })
    except Exception as e:
        print(f"EXCEPTION in /finalize-report: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/load-master-excel', methods=['POST'])
def load_master_excel_route():
    try:
        if 'excel_file' not in request.files:
            return jsonify({"error": "No Excel file"}), 400
        excel_file = request.files['excel_file']
        excel_path = os.path.join(UPLOAD_DIR, 'MASTER_AUDIT_DATA.xlsx')
        excel_file.save(excel_path)

        # Load tables from Excel into structured format
        xls = pd.ExcelFile(excel_path)
        tables = {}
        for sheet in xls.sheet_names:
            df = pd.read_excel(excel_path, sheet_name=sheet)
            records = df.where(pd.notnull(df), None).values.tolist()
            records_dicts = []
            for row in records:
                row_dict = {str(col): row[i] for i, col in enumerate(df.columns)}
                records_dicts.append(row_dict)
            tables[sheet] = records_dicts

        return jsonify({"tables": sanitize_for_json(tables)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/load-existing-master-excel', methods=['GET'])
def load_existing_master_excel():
    try:
        excel_path = os.path.join(OUTPUT_DIR, 'MASTER_AUDIT_DATA.xlsx')
        if not os.path.exists(excel_path):
            return jsonify({"error": "No MASTER_AUDIT_DATA.xlsx found"}), 404

        xls = pd.ExcelFile(excel_path)
        tables = {}
        for sheet in xls.sheet_names:
            df = pd.read_excel(excel_path, sheet_name=sheet)
            records_dicts = []
            for _, row in df.iterrows():
                row_dict = {str(col): (None if pd.isna(val) else val) for col, val in row.items()}
                records_dicts.append(row_dict)
            tables[sheet] = records_dicts

        return jsonify({"tables": sanitize_for_json(tables)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/download/<filename>')
def download(filename):
    return send_from_directory(OUTPUT_DIR, filename)

if __name__ == '__main__':
    app.run(debug=True, port=5050, host='0.0.0.0')
