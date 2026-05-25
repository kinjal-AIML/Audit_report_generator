from typing import Dict, List
import os
import pandas as pd

try:
    from docx import Document
except Exception:  # pragma: no cover
    Document = None


def extract_tables_from_docx(file_path: str) -> Dict[str, pd.DataFrame]:
    """
    Extract all tables from a DOCX file and return a mapping of
    sheet name -> DataFrame. If there are no tables, returns empty dict.
    Sheet names are generated as 'Master DOCX - Table N'.
    """
    results: Dict[str, pd.DataFrame] = {}
    if not Document:
        return results

    try:
        doc = Document(file_path)
        table_index = 1
        for t in doc.tables:
            rows: List[dict] = []
            headers: List[str] = []

            # Derive headers from first row when possible
            if len(t.rows) > 0:
                first_cells = t.rows[0].cells
                headers = [c.text.strip() or f"Col_{i}" for i, c in enumerate(first_cells)]
                data_rows = t.rows[1:]
            else:
                data_rows = []

            if not headers and len(t.columns) > 0:
                headers = [f"Col_{i}" for i in range(len(t.columns))]

            for row in data_rows:
                values = [c.text.strip() for c in row.cells]
                # pad or trim values to headers length
                if len(values) < len(headers):
                    values += [""] * (len(headers) - len(values))
                elif len(values) > len(headers):
                    values = values[:len(headers)]
                rows.append(dict(zip(headers, values)))

            if rows:
                df = pd.DataFrame(rows)
                if 'Remarks' not in df.columns:
                    df['Remarks'] = ''
                if 'Annexure Ref' not in df.columns:
                    df['Annexure Ref'] = ''
                results[f"Master DOCX - Table {table_index}"] = df
                table_index += 1

        return results
    except Exception:
        return {}
