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

@app.route('/extract-data', methods=['POST'])
def extract_data_route():
    try:
        if 'audit_file' not in request.files:
            return jsonify({"error": "No audit file uploaded"}), 400
        
        audit_file = request.files['audit_file']
        start_date = request.form.get('start_date')
        
        audit_path = os.path.join(UPLOAD_DIR, audit_file.filename)
        audit_file.save(audit_path)
        
        pdf_files = request.files.getlist('pdf_files')
        for f in pdf_files:
            if f.filename:
                f.save(os.path.join(UPLOAD_DIR, f.filename))
        
        file_mappings = get_file_mappings(pdf_files)

        # Extract from audit DOCX
        if "CNSB" in audit_file.filename.upper():
            data = extract_cnsb_data(audit_path)
            template_name = "UPDATED_CNSB_TEMPLATE.docx"
        elif "MNSB" in audit_file.filename.upper():
            data = extract_mnsb_data(audit_path)
            template_name = "UPDATED_MNSB_TEMPLATE.docx"
        else:
            template_name = "UPDATED_CNSB_TEMPLATE.docx"
            data = {}

        if not start_date:
            start_date = "2026-02-01"
        
        # Extract cash verification date and closing balance from Cash report PDF
        cash_verification_date = None
        closing_cash_balance = None
        closing_cash_balance_words = None
        
        for sheet_name, filename in file_mappings.items():
            file_path = os.path.join(UPLOAD_DIR, filename)
            if os.path.exists(file_path) and "cash" in sheet_name.lower():
                cash_df = extract_cash_summary(file_path)
                if not cash_df.empty:
                    cash_verification_date = cash_df.attrs.get("report_date", "")
                    closing_rows = cash_df[cash_df["Description"] == "Closing Cash Balance"]
                    if not closing_rows.empty:
                        closing_cash_balance = closing_rows.iloc[0]["Amount (INR)"]
                        closing_cash_balance_words = number_to_indian_rupees(closing_cash_balance)

        date_context = build_template_context("Branch X", "Ahmedabad", start_date, cash_verification_date)
        data.update(date_context)
        
        # Update with extracted cash values if available
        if closing_cash_balance:
            data["closing_cash_balance"] = closing_cash_balance
            data["closing_cash_balance_words"] = closing_cash_balance_words

        placeholders = {
            "npa_summary": "NPA accounts review completed.",
            "annexure_reference": "See Annexure A",
            "audit_observation": "Observations recorded in master data sheet.",
            "closing_cash_balance": data.get("closing_cash_balance", "0.00")
        }
        data.update(placeholders)

        docx_excel_url = None
        try:
            docx_excel_path = generate_docx_like_excel(audit_path, OUTPUT_DIR)
            docx_excel_url = f"/download/{os.path.basename(docx_excel_path)}"
        except: pass

        pdf_results = process_all_pdfs(UPLOAD_DIR, file_mappings)
        
        master_excel_file = request.files.get('master_excel_file')
        if master_excel_file and master_excel_file.filename.endswith('.xlsx'):
            master_excel_path = os.path.join(UPLOAD_DIR, master_excel_file.filename)
            master_excel_file.save(master_excel_path)
            try:
                master_excel_data = pd.read_excel(master_excel_path, sheet_name=None)
                for sheet_name, df in master_excel_data.items():
                    pdf_results[sheet_name] = df
            except: pass
        
        npa_df = pdf_results.get("NPA Accounts", pd.DataFrame())
        if not npa_df.empty:
            placeholders["npa_summary"] = f"A total of {len(npa_df)} NPA accounts were identified."

        sanitized_tables = {k: sanitize_for_json(v.to_dict(orient='records')) for k, v in pdf_results.items()}
        review_data = {"master_data": sanitize_for_json(data), "tables": sanitized_tables}
        session['template_name'] = template_name
        
        return jsonify({"message": "Data extracted successfully", "data": review_data, "files": {"docx_excel": docx_excel_url} if docx_excel_url else {}})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/extract-excel-docx', methods=['POST'])
def extract_excel_docx_route():
    try:
        if 'audit_file' not in request.files: return jsonify({"error": "No audit file"}), 400
        audit_file = request.files['audit_file']
        audit_path = os.path.join(UPLOAD_DIR, audit_file.filename)
        audit_file.save(audit_path)
        excel_path = generate_docx_like_excel(audit_path, OUTPUT_DIR)
        return jsonify({"message": "Generated successfully", "file": f"/download/{os.path.basename(excel_path)}"})
    except Exception as e: return jsonify({"error": str(e)}), 500

@app.route('/extract-excel-pdf', methods=['POST'])
def extract_excel_pdf_route():
    try:
        pdf_files = request.files.getlist('pdf_files')
        if not pdf_files: return jsonify({"error": "No PDF files"}), 400
        for f in pdf_files:
            if f.filename: f.save(os.path.join(UPLOAD_DIR, f.filename))
        
        file_mappings = get_file_mappings(pdf_files)
        pdf_results = process_all_pdfs(UPLOAD_DIR, file_mappings)
        excel_path = generate_master_excel(pdf_results, OUTPUT_DIR)
        return jsonify({"message": "Generated successfully", "file": f"/download/{os.path.basename(excel_path)}"})
    except Exception as e: return jsonify({"error": str(e)}), 500

@app.route('/download-excel-now', methods=['POST'])
def download_excel_now_route():
    try:
        payload = request.json or {}
        table_data = payload.get('table_data') or {}
        excel_data = {k: pd.DataFrame(v) for k, v in table_data.items()}
        excel_path = generate_master_excel(excel_data, OUTPUT_DIR)
        return jsonify({"message": "Generated successfully", "file": f"/download/{os.path.basename(excel_path)}"})
    except Exception as e: return jsonify({"error": str(e)}), 500

@app.route('/finalize-report', methods=['POST'])
def finalize_report_route():
    try:
        form_data = request.json
        master_data = form_data.get('master_data')
        table_data = form_data.get('table_data')
        template_name = session.get('template_name', 'UPDATED_CNSB_TEMPLATE.docx')
        
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
        
        master_data['annexure_summaries'] = "\\n".join(summaries)
        master_data['annexure_count'] = len(summaries)
        master_data['insurance_pending'] = insurance_list
        master_data['overdue_summary'] = overdue_summary_list
        
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
        if template_name == "UPDATED_MNSB_TEMPLATE.docx":
            final_template = "UPDATED_MNSB_TEMPLATE_DYNAMIC.docx"
            
        output_docx = generate_report(template_name=final_template, context=master_data)
        return jsonify({
            "message": "Generated successfully",
            "files": {
                "docx": f"/download/{os.path.basename(output_docx)}",
                "pdf": f"/download/{os.path.basename(output_docx.replace('.docx', '.pdf'))}",
                "excel": f"/download/{os.path.basename(excel_path)}",
                "annexure": f"/download/{os.path.basename(annexure_path)}"
            }
        })
    except Exception as e: return jsonify({"error": str(e)}), 500

@app.route('/load-master-excel', methods=['POST'])
def load_master_excel_route():
    try:
        excel_file = request.files.get('excel_file')
        if not excel_file: return jsonify({"error": "No file"}), 400
        excel_path = os.path.join(UPLOAD_DIR, excel_file.filename)
        excel_file.save(excel_path)
        excel_data = pd.read_excel(excel_path, sheet_name=None)
        tables = {s: sanitize_for_json(df.to_dict(orient='records')) for s, df in excel_data.items()}
        return jsonify({"message": "Loaded successfully", "tables": tables})
    except Exception as e: return jsonify({"error": str(e)}), 500

@app.route('/load-existing-master-excel', methods=['GET'])
def load_existing_master_excel_route():
    try:
        import glob
        files = glob.glob(os.path.join(OUTPUT_DIR, "MASTER_AUDIT_DATA.xlsx"))
        if not files: return jsonify({"error": "Not found"}), 404
        excel_data = pd.read_excel(files[0], sheet_name=None)
        tables = {s: sanitize_for_json(df.to_dict(orient='records')) for s, df in excel_data.items()}
        return jsonify({"message": "Loaded successfully", "tables": tables})
    except Exception as e: return jsonify({"error": str(e)}), 500

@app.route('/download/<filename>')
def download_report(filename):
    return send_from_directory(OUTPUT_DIR, filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True, port=5050)
