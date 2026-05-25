from docxtpl import DocxTemplate
from pathlib import Path
from typing import Dict, Any
import os
import gc
from utils.logger import logger

class WordTemplateAutomationEngine:
    """
    Module 12 & 13 & 15: Word Template Automation & Export Engine
    Uses DOCXTPL to safely inject variables without corrupting DOCX internals.
    Also handles Annexure generation implicitly.
    """
    def __init__(self, templates_dir: str = "templates", exports_dir: str = "exports"):
        self.templates_dir = Path(templates_dir)
        self.exports_dir = Path(exports_dir)
        self.docx_dir = self.exports_dir / "docx"
        self.pdf_dir = self.exports_dir / "pdf"
        
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        self.docx_dir.mkdir(parents=True, exist_ok=True)
        self.pdf_dir.mkdir(parents=True, exist_ok=True)

    def render_template(self, template_name: str, context: Dict[str, Any], output_name: str) -> str:
        """
        Loads the docx template, injects the context dict directly where placeholders exist.
        """
        template_path = self.templates_dir / template_name
        output_path = self.docx_dir / output_name
        
        if not template_path.exists():
            raise FileNotFoundError(f"Template {template_name} not found in {self.templates_dir}")
            
        logger.info(f"Rendering docx template {template_name} -> {output_name}")
        doc = DocxTemplate(str(template_path))
        doc.render(context)
        doc.save(str(output_path))
        
        # force cleanup of template in memory to prevent lxml handle leaks
        del doc
        gc.collect() 
        
        return str(output_path)
        
    def export_to_pdf(self, docx_path: str, output_pdf_name: str) -> str:
        """
        Module 15: DOCX/PDF Export Engine (converting Docx to PDF)
        Uses docx2pdf. Fails safely on Linux, requires MS Word on Windows.
        """
        output_path = self.pdf_dir / output_pdf_name
        logger.info(f"Converting DOCX to PDF: {output_path}")
        try:
            from docx2pdf import convert
            convert(docx_path, str(output_path))
            return str(output_path)
        except Exception as e:
            logger.error(f"Failed to convert Docx to PDF. Please ensure MS Word is installed. Error: {e}")
            return docx_path # Fallback response
