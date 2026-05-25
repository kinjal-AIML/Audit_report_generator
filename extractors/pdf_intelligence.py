import pdfplumber
import fitz  # PyMuPDF
from pathlib import Path
from utils.logger import logger
from typing import Dict, Any, List

class PDFIntelligenceEngine:
    """
    Module 1: PDF Intelligence Engine
    Detects digital vs scanned PDFs, preserves coordinates and structure using PyMuPDF and pdfplumber.
    """
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        if not self.file_path.exists():
            raise FileNotFoundError(f"PDF file not found: {self.file_path}")
        
    def analyze_pdf_type(self) -> Dict[str, Any]:
        """
        Determines if the PDF is digital (ERP generated), scanned, or mixed.
        Returns metadata containing page counts and type.
        """
        logger.info(f"Analyzing PDF type for {self.file_path.name}")
        page_count = 0
        text_pages = 0
        
        with fitz.open(str(self.file_path)) as doc:
            page_count = len(doc)
            for page in doc:
                text = page.get_text("text").strip()
                if len(text) > 50:  # Arbitrary threshold to determine if text exists
                    text_pages += 1
                    
        pdf_type = "ERROR"
        if text_pages == page_count:
            pdf_type = "DIGITAL_ERP"
        elif text_pages == 0:
            pdf_type = "SCANNED"
        else:
            pdf_type = "MIXED"
            
        metadata = {
            "file_name": self.file_path.name,
            "page_count": page_count,
            "text_pages": text_pages,
            "pdf_type": pdf_type
        }
        logger.debug(f"PDF Analysis Result: {metadata}")
        return metadata

    def extract_raw_layout(self) -> List[Dict[str, Any]]:
        """
        Extracts raw text dictionaries with bounding boxes from digital PDFs.
        Preserves natural reading order and block hierarchy.
        """
        logger.info(f"Extracting raw layout for {self.file_path.name}")
        layout_data = []
        with fitz.open(str(self.file_path)) as doc:
            for page_num, page in enumerate(doc):
                blocks = page.get_text("dict")["blocks"]
                for block in blocks:
                    if "lines" in block:
                        for line in block["lines"]:
                            for span in line["spans"]:
                                layout_data.append({
                                    "page": page_num,
                                    "bbox": span["bbox"],
                                    "text": span["text"].strip(),
                                    "font": span["font"],
                                    "size": span["size"]
                                })
        return layout_data
