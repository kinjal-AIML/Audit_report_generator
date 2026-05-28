from docx import Document
from docx.text.paragraph import Paragraph as DocxParagraph
from docx.table import Table as DocxTable

path = r"D:\audit_report_generator\uploads\MNSB Panchot January 26.docx"

doc = Document(path)
body = doc.element.body

last_heading = None
sec_idx = 0

def is_heading(p):
    try:
        style_name = getattr(getattr(p, "style", None), "name", "") or ""
        if style_name.startswith("Heading"):
            return True
        txt = (p.text or "").strip()
        if len(txt) >= 6 and txt.isupper():
            return True
    except Exception:
        pass
    return False

for el in body.iterchildren():
    tag = el.tag.rsplit('}', 1)[-1]
    if tag == 'p':
        p = DocxParagraph(el, doc)
        if is_heading(p):
            sec_idx += 1
            last_heading = p.text.strip()
    elif tag == 'tbl':
        t = DocxTable(el, doc)
        headers = []
        if t.rows:
            headers = [c.text.strip() for c in t.rows[0].cells]
        print(f"Section[{sec_idx}]: {last_heading!r} | Headers: {headers}")
