# Dynamic DOCX Template Guide (DocxTpl)

Use this guide to ensure your template shows UI-entered Auditor Remarks and Branch Replies correctly.

## Key Variables Per Question
- Question text: `{{ q.audit_review }}` (alias of `{{ q.question }}`)
- Auditor Remark (from UI): `{{ q.auditor_comment }}` (alias of `{{ q.remark }}`)
- Branch Reply (from UI): `{{ q.branch_reply }}`

## Recommended Structure (Sections → Questions)
Most templates render a list of sections, each with a table of questions.

### Option A: Paragraph layout
```
{% for section in sections %}
{{ section.section_name }}

{% for q in section.questions %}
• {{ q.audit_review }}
  - Auditor Remark: {{ q.auditor_comment }}
  - Reply of Branch: {{ q.branch_reply }}
{% endfor %}

{% endfor %}
```

### Option B: Table layout (row duplication)
DocxTpl duplicates the entire table row that contains a `{% for ... %}` and `{% endfor %}` pair. Place both tags in cells within the same row.

- Header row (static):
  - Sr | Audit Review | Auditor Remark | Reply of Branch
- Next row (the loop row):
  - Cell 1: `{% for q in section.questions %}{{ q.sr_no }}`
  - Cell 2: `{{ q.audit_review }}`
  - Cell 3: `{{ q.auditor_comment }}`
  - Cell 4: `{{ q.branch_reply }}{% endfor %}`

Wrap the whole table with a per-section loop if you have multiple sections:
```
{% for section in sections %}
{{ section.section_name }}

| Sr | Audit Review | Auditor Remark | Reply of Branch |
|----|--------------|----------------|-----------------|
| {% for q in section.questions %}{{ q.sr_no }} | {{ q.audit_review }} | {{ q.auditor_comment }} | {{ q.branch_reply }}{% endfor %} |

{% endfor %}
```
Note: The example above uses Markdown for readability; in Word, insert the `{% for %}` in the first data row and `{% endfor %}` in the last cell of that same row.

## Helpful Jinja Patterns
- Show "Nil" when remark is empty:
  - `{{ q.auditor_comment if q.auditor_comment else 'Nil' }}`
- Add line breaks:
  - Prefer simple one-line fields. If multi-line needed, insert hard returns in UI; DocxTpl preserves paragraph breaks.

## Common Pitfalls
- Curly braces: Ensure standard ASCII `{` and `}` are used (Word sometimes autocorrects quotes; disable smart quotes if needed).
- Spaces: Avoid extra spaces inside `{{ ... }}` or `{% ... %}`.
- Loop placement: The `{% for %}` and `{% endfor %}` must live in the same row to duplicate that row.
- Case-sensitivity: Backend is tolerant, but prefer the exact names shown above.

## Quick Test
1. Replace `templates/UPDATED_MNSB_TEMPLATE_DYNAMIC.docx` with your template.
2. Run the app, enter a few Auditor Remarks in Step 2.
3. Finalize and open the generated DOCX.

You should see the Auditor Remarks under the corresponding column/cell.
