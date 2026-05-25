from docxtpl import DocxTemplate
import os
from datetime import datetime

OUTPUT_DIR = "outputs"


def generate_report(template_name, context):

    template_path = os.path.join(
        "templates",
        template_name
    )

    doc = DocxTemplate(template_path)

    doc.render(context)

    filename = f"AUDIT_{datetime.now().timestamp()}.docx"

    output_path = os.path.join(
        OUTPUT_DIR,
        filename
    )

    doc.save(output_path)

    # Generate Final PDF Report (Step 10)
    try:
        from docx2pdf import convert
        pdf_path = output_path.replace(".docx", ".pdf")
        # convert(output_path, pdf_path) # Commented out as it requires Microsoft Word installed
        print(f"PDF generated: {pdf_path}")
    except Exception as e:
        print(f"PDF conversion failed: {str(e)}")

    return output_path