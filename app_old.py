from flask import Flask, render_template, request, jsonify, send_from_directory, session
from flask_cors import CORS
import os
import shutil
import json
import re
import pandas as pd
from extractors.cnsb_extractor import extract_cnsb_data
from extractors.mnsb_extractor import extract_mnsb_data
from extractors.pdf_extractor import process_all_pdfs
from extractors.docx_table_extractor import extract_tables_from_docx
from generators.report_generator import generate_report
from utils.date_utils import parse_date, format_date, build_template_context
from utils.excel_generator import generate_master_excel, generate_annexure_workbook
from utils.docx_to_excel import generate_docx_like_excel

app = Flask(__name__)
app.secret_key = "supersecretkey" # For session storage
CORS(app)

UPLOAD_DIR = "uploads"
OUTPUT_DIR = "outputs"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

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
        
        # Handle supporting PDFs with improved keyword matching
        pdf_files = request.files.getlist('pdf_files')
        file_mappings = {}
        for f in pdf_files:
            if not f.filename:
                continue
            pdf_path = os.path.join(UPLOAD_DIR, f.filename)
            f.save(pdf_path)
            name_lower = f.filename.lower()
            
            # Flexible keyword detection (supports spaces, hyphens)
            if re.search(r'insurance', name_lower):
                file_mappings["Insurance Pending Register"] = f.filename
            elif re.search(r'cash', name_lower):
                file_mappings["Cash report"] = f.filename
            elif re.search(r'npa', name_lower):
                file_mappings["NPA Accounts"] = f.filename
            elif re.search(r'over\s*due|overdue', name_lower):   # handles "over due", "overdue", "over-due"
                file_mappings["Loan Overdue"] = f.filename
            elif re.search(r'recovery', name_lower):
                file_mappings["Recovery Accounts"] = f.filename
            else:
                file_mappings[os.path.splitext(f.filename)[0]] = f.filename

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
        date_context = build_template_context("Branch X", "Ahmedabad", start_date)
        data.update(date_context)

        placeholders = {
            "npa_summary": "NPA accounts review completed. Found items listed in Annexure.",
            "annexure_reference": "See Annexure A",
            "audit_observation": "Observations recorded in master data sheet.",
            "closing_cash_balance": data.get("closing_cash_balance", "0.00")
        }
        data.update(placeholders)

        try:
            docx_excel_path = generate_docx_like_excel(audit_path, OUTPUT_DIR)
            docx_excel_url = f"/download/{os.path.basename(docx_excel_path)}"
        except Exception:
            docx_excel_url = None

        pdf_results = process_all_pdfs(UPLOAD_DIR, file_mappings)
        
        npa_df = pdf_results.get("NPA Accounts", pd.DataFrame())
        if not npa_df.empty:
            total_npa = len(npa_df)
            placeholders["npa_summary"] = f"A total of {total_npa} NPA accounts were identified during this period. Detailed observations for each account are captured in the master audit data sheet."

        import numpy as np
        def sanitize_for_json(obj):
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

        sanitized_tables = {}
        for k, v in pdf_results.items():
            records = v.to_dict(orient='records')
            sanitized_tables[k] = sanitize_for_json(records)

        review_data = {
            "master_data": sanitize_for_json(data),
            "tables": sanitized_tables
        }

        session['template_name'] = template_name
        
        return jsonify({
            "message": "Data extracted successfully",
            "data": review_data,
            "files": {"docx_excel": docx_excel_url} if docx_excel_url else {}
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/extract-excel-docx', methods=['POST'])
def extract_excel_docx_route():
    """Generate Excel from Master DOCX preserving document structure in a single sheet."""
    try:
        if 'audit_file' not in request.files:
            return jsonify({"error": "No audit file uploaded"}), 400

        audit_file = request.files['audit_file']
        audit_path = os.path.join(UPLOAD_DIR, audit_file.filename)
        audit_file.save(audit_path)

        # Create a single-sheet Excel approximating the DOCX layout
        excel_path = generate_docx_like_excel(audit_path, OUTPUT_DIR)
        return jsonify({
            "message": "DOCX to Excel generated successfully",
            "file": f"/download/{os.path.basename(excel_path)}"
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/extract-excel-pdf', methods=['POST'])
def extract_excel_pdf_route():
    """Generate Excel containing only tables extracted from uploaded PDFs."""
    try:
        pdf_files = request.files.getlist('pdf_files')
        if not pdf_files:
            return jsonify({"error": "No PDF files uploaded"}), 400

        file_mappings = {}
        for f in pdf_files:
            if not f.filename:
                continue
            pdf_path = os.path.join(UPLOAD_DIR, f.filename)
            f.save(pdf_path)
            name = f.filename.lower()
            if "insurance" in name:
                file_mappings["Insurance Pending Register"] = f.filename
            elif "cash" in name:
                file_mappings["Cash report"] = f.filename
            elif "npa" in name:
                file_mappings["NPA Accounts"] = f.filename
            elif "overdue" in name:
                file_mappings["Loan Overdue"] = f.filename
            elif "recovery" in name:
                file_mappings["Recovery Accounts"] = f.filename
            else:
                file_mappings[os.path.splitext(f.filename)[0]] = f.filename

        pdf_results = process_all_pdfs(UPLOAD_DIR, file_mappings)
        excel_path = generate_master_excel(pdf_results, OUTPUT_DIR)
        return jsonify({
            "message": "PDFs to Excel generated successfully",
            "file": f"/download/{os.path.basename(excel_path)}"
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/download-excel-now', methods=['POST'])
def download_excel_now_route():
    """
    Generate Excel from the current preview tables sent as JSON.
    Body: { table_data: { sheet: [ {col:val} ] } }
    """
    try:
        payload = request.json or {}
        table_data = payload.get('table_data') or {}
        excel_data = {}
        for k, v in table_data.items():
            excel_data[k] = pd.DataFrame(v)

        excel_path = generate_master_excel(excel_data, OUTPUT_DIR)
        return jsonify({
            "message": "Excel generated successfully",
            "file": f"/download/{os.path.basename(excel_path)}"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/finalize-report', methods=['POST'])
def finalize_report_route():
    form_data = request.json
    master_data = form_data.get('master_data')
    table_data = form_data.get('table_data') # Dictionary of lists
    template_name = session.get('template_name', 'UPDATED_CNSB_TEMPLATE.docx')

    # 1. Generate Master Excel
    excel_data = {}
    for k, v in table_data.items():
        excel_data[k] = pd.DataFrame(v)
    
    excel_path = generate_master_excel(excel_data, OUTPUT_DIR)
    annexure_path = generate_annexure_workbook(excel_data, OUTPUT_DIR)

    # 2. Generate Final DOCX
    # Update master_data with summaries if needed
    # Example: master_data["npa_summary"] = "Summary of NPA..."
    
    try:
        output_docx = generate_report(
            template_name=template_name,
            context=master_data
        )
        
        # 3. Generate PDF (Step 10)
        # Placeholder for PDF generation
        output_pdf = output_docx.replace(".docx", ".pdf")
        
        return jsonify({
            "message": "All reports generated successfully",
            "files": {
                "docx": f"/download/{os.path.basename(output_docx)}",
                "pdf": f"/download/{os.path.basename(output_docx.replace('.docx', '.pdf'))}",
                "excel": f"/download/{os.path.basename(excel_path)}",
                "annexure": f"/download/{os.path.basename(annexure_path)}"
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/generate-report', methods=['POST'])
def generate_audit_report():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')

    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    file_path = os.path.join(UPLOAD_DIR, file.filename)
    file.save(file_path)

    # Detect template type
    if "CNSB" in file.filename.upper():
        data = extract_cnsb_data(file_path)
        template_name = "UPDATED_CNSB_TEMPLATE.docx"
    elif "MNSB" in file.filename.upper():
        data = extract_mnsb_data(file_path)
        template_name = "UPDATED_MNSB_TEMPLATE.docx"
    else:
        return jsonify({"error": "Unsupported report type"}), 400

    # Format dates to dd-mm-yyyy for the report
    try:
        data["period_start"] = format_date(parse_date(start_date))
        data["period_end"] = format_date(parse_date(end_date))
    except Exception as e:
        return jsonify({"error": f"Invalid date format: {str(e)}"}), 400

    try:
        output_path = generate_report(
            template_name=template_name,
            context=data
        )
        return jsonify({
            "message": "Report generated successfully",
            "download_url": f"/download/{os.path.basename(output_path)}"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/download/<filename>')
def download_report(filename):
    return send_from_directory(OUTPUT_DIR, filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
