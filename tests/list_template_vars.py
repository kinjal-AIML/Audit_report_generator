from docxtpl import DocxTemplate
import os
import json

tpl_path = os.path.join('templates', 'UPDATED_MNSB_TEMPLATE_DYNAMIC.docx')

if not os.path.exists(tpl_path):
    print(json.dumps({"error": f"Template not found: {tpl_path}"}))
    raise SystemExit(2)

doc = DocxTemplate(tpl_path)
# Empty context: we want undeclared variables as-is
vars_set = doc.get_undeclared_template_variables({})
print(json.dumps({
    "template": tpl_path,
    "variable_count": len(vars_set),
    "variables": sorted(list(vars_set))
}, indent=2))
