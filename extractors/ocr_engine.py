from paddleocr import PaddleOCR
from pdf2image import convert_from_path
import numpy as np
from pathlib import Path
from utils.logger import logger
from typing import List, Dict, Any

class OCREngine:
    """
    Module 2: OCR Engine
    Uses PaddleOCR to extract text and bounding boxes from scanned banking PDFs.
    """
    def __init__(self, lang='en'):
        # use_angle_cls=True to rotate skewed pages automatically
        logger.info("Initializing PaddleOCR Engine")
        self.ocr = PaddleOCR(use_angle_cls=True, lang=lang, show_log=False)
        
    def extract_from_pdf(self, pdf_path: str) -> List[Dict[str, Any]]:
        """
        Converts PDF to images and extracts coordinates, text, and confidence.
        """
        logger.info(f"Extracting OCR from PDF: {pdf_path}")
        results = []
        path = Path(pdf_path)
        if not path.exists():
            raise FileNotFoundError(f"File {pdf_path} not found.")

        # Convert PDF pages to PIL images (Requires Poppler to be installed on system)
        try:
            images = convert_from_path(str(path))
        except Exception as e:
            logger.error(f"Failed to convert PDF to image: {e}. Is Poppler installed?")
            return []

        for page_idx, img in enumerate(images):
            # Convert PIL image to numpy array for PaddleOCR
            img_np = np.array(img)
            # result structure: [[[[x,y], [x,y], [x,y], [x,y]], ('text', confidence)], ...]
            ocr_result = self.ocr.ocr(img_np, cls=True)
            
            if not ocr_result or not ocr_result[0]:
                continue
                
            for res in ocr_result[0]:
                coords, (text, conf) = res
                results.append({
                    "page": page_idx,
                    "bbox": coords,  # 4 points
                    "text": text,
                    "confidence": conf
                })
                
        logger.info(f"OCR extracted {len(results)} layout elements.")
        return results
