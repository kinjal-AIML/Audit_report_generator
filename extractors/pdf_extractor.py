import pdfplumber
import pandas as pd
import os
from typing import List

# Optional imports: camelot and tabula offer stronger table extraction
try:
    import camelot
except Exception:  # pragma: no cover
    camelot = None

try:
    import tabula
except Exception:  # pragma: no cover
    tabula = None

# Optional OCR fallback for image-based PDFs
try:
    import pytesseract  # Requires local Tesseract installation
    from pdf2image import convert_from_path
    from PIL import Image
except Exception:  # pragma: no cover
    pytesseract = None
    convert_from_path = None
    Image = None

def _extract_with_pdfplumber(file_path: str) -> List[pd.DataFrame]:
    frames: List[pd.DataFrame] = []
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables({
                "vertical_strategy": "text",
                "horizontal_strategy": "text",
                "snap_tolerance": 3,
            })
            for table in tables or []:
                if table and len(table) > 1:
                    df = pd.DataFrame(table[1:], columns=table[0])
                    df.columns = [str(c).replace("\n", " ").strip() if c else f"Col_{i}" for i, c in enumerate(df.columns)]
                    frames.append(df)
    return frames


def _extract_with_camelot(file_path: str) -> List[pd.DataFrame]:
    frames: List[pd.DataFrame] = []
    if not camelot:
        return frames
    try:
        # Try lattice first (explicit table borders), then stream (whitespace)
        for flavor in ("lattice", "stream"):
            try:
                tables = camelot.read_pdf(file_path, pages="all", flavor=flavor)
                for t in tables:
                    df = t.df
                    # Use first row as header if it looks like headers
                    if df.shape[0] > 1:
                        header = df.iloc[0].tolist()
                        df = df[1:]
                        df.columns = [str(c).replace("\n", " ").strip() for c in header]
                    frames.append(df.reset_index(drop=True))
            except Exception:
                continue
    except Exception:
        pass
    return frames


def _extract_with_tabula(file_path: str) -> List[pd.DataFrame]:
    frames: List[pd.DataFrame] = []
    if not tabula:
        return frames
    try:
        # multiple_tables=True returns list of DataFrames
        for lattice in (True, False):
            try:
                dfs = tabula.read_pdf(file_path, pages="all", multiple_tables=True, lattice=lattice, stream=not lattice)
                for df in dfs or []:
                    if not df.empty:
                        # Clean header-like first row
                        if df.shape[0] > 1 and any(isinstance(v, str) for v in df.iloc[0].tolist()):
                            header = [str(c).replace("\n", " ").strip() for c in df.iloc[0].tolist()]
                            df = df[1:]
                            df.columns = header
                        frames.append(df.reset_index(drop=True))
            except Exception:
                continue
    except Exception:
        pass
    return frames


def _extract_with_ocr(file_path: str) -> List[pd.DataFrame]:
    frames: List[pd.DataFrame] = []
    if not (pytesseract and convert_from_path):
        return frames
    try:
        images = convert_from_path(file_path)
        rows = []
        for img in images:
            text = pytesseract.image_to_string(img)
            for line in text.splitlines():
                line = line.strip()
                if line:
                    rows.append({"Text": line})
        if rows:
            frames.append(pd.DataFrame(rows))
    except Exception:
        pass
    return frames


def extract_pdf_data(file_path, report_type):
    """
    Extract structured data from PDF reports.
    Strategy:
    1) pdfplumber tables
    2) camelot (lattice/stream)
    3) tabula (lattice/stream)
    4) OCR fallback to single-column text
    """
    print(f"Opening PDF: {file_path}")
    frames: List[pd.DataFrame] = []

    # Try multiple strategies in order
    try:
        frames.extend(_extract_with_pdfplumber(file_path))
    except Exception as e:
        print(f"pdfplumber failed for {file_path}: {e}")

    if not frames:
        frames.extend(_extract_with_camelot(file_path))

    if not frames:
        frames.extend(_extract_with_tabula(file_path))

    if not frames:
        frames.extend(_extract_with_ocr(file_path))

    if not frames:
        return pd.DataFrame()

    final_df = pd.concat(frames, ignore_index=True)
    final_df = final_df.dropna(how='all')

    if 'Remarks' not in final_df.columns:
        final_df['Remarks'] = ""
    if 'Annexure Ref' not in final_df.columns:
        final_df['Annexure Ref'] = ""

    return final_df

def process_all_pdfs(upload_dir, file_mappings):
    """
    Processes all uploaded PDFs and returns a dictionary of DataFrames.
    file_mappings: { 'insurance': 'file1.pdf', 'loan_overdue': 'file2.pdf', ... }
    """
    results = {}
    for report_type, filename in file_mappings.items():
        file_path = os.path.join(upload_dir, filename)
        if os.path.exists(file_path):
            results[report_type] = extract_pdf_data(file_path, report_type)
    return results
