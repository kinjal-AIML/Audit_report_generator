import json
import os
import sys

# Ensure workspace root on path
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from utils.template_parser import parse_docx_template


def main():
    path = r"D:\audit_report_generator\uploads\MNSB Panchot January 26.docx"
    if not os.path.exists(path):
        print(json.dumps({"error": f"File not found: {path}"}, ensure_ascii=False))
        sys.exit(2)
    data = parse_docx_template(path)
    # Summarize to keep output readable
    summary = {
        "section_count": len(data.get("sections", [])),
        "sections": []
    }
    for s in data.get("sections", []):
        section_entry = {
            "name": s.get("section_name"),
            "question_count": len(s.get("questions", [])),
            "samples": []
        }
        for q in s.get("questions", [])[:3]:
            section_entry["samples"].append({
                "sr_no": q.get("sr_no"),
                "key": q.get("key"),
                "question": (q.get("question") or "")[:160],
                "has_remark": bool(q.get("remark")),
                "has_branch_reply": bool(q.get("branch_reply")),
                "annexure_reference": q.get("annexure_reference"),
            })
        summary["sections"].append(section_entry)
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
