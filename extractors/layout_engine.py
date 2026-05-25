import pdfplumber
import camelot
from typing import List, Dict, Any, Tuple
from pathlib import Path
from utils.logger import logger

class LayoutIntelligenceEngine:
    """
    Module 4 & 6: Document Layout Intelligence & Table Structure Recognition Engine
    Segment boundaries, table detection using Camelot/pdfplumber, and structure preservation.
    """
    def __init__(self, use_layout_parser: bool = False):
        self.use_layout_parser = use_layout_parser
        if use_layout_parser:
            try:
                import layoutparser as lp
                # Use detectron2 only as advanced fallback if properly installed in env
                self.model = lp.Detectron2LayoutModel(
                    config_path='lp://PubLayNet/mask_rcnn_X_101_32x8d_FPN_3x/config',
                    extra_config=["MODEL.ROI_HEADS.SCORE_THRESH_TEST", 0.8],
                    label_map={0: "Text", 1: "Title", 2: "List", 3: "Table", 4: "Figure"}
                )
            except ImportError:
                logger.warning("layoutparser or detectron2 not found. Falling back to pdfplumber/camelot heuristics.")
                self.use_layout_parser = False

    def detect_tables_camelot(self, pdf_path: str, pages: str = 'all') -> List[Dict]:
        """
        Extracts structured table frames using Camelot.
        Handles grid structures and complex spans.
        """
        logger.info(f"Extracting tables from {pdf_path} using Camelot")
        try:
            tables = camelot.read_pdf(pdf_path, pages=pages, flavor='stream', suppress_stdout=True)
            results = []
            for idx, table in enumerate(tables):
                results.append({
                    "table_index": idx,
                    "page": table.page,
                    "bbox": table._bbox,
                    "df": table.df  # raw pandas dataframe before coordinate mapping
                })
            return results
        except Exception as e:
            logger.error(f"Camelot table extraction failed: {e}")
            return []

    def perform_layout_analysis(self, pdf_path: str) -> Dict[str, Any]:
        """
        Combined layout analysis for extracting text blocks and identifying tables/headers.
        """
        if self.use_layout_parser:
            return self._layoutparser_analysis(pdf_path)
            
        # Fallback to pdfplumber-based bounding heuristics
        logger.info(f"Performing heuristic layout analysis on {pdf_path}")
        layout_elements = {"headers": [], "footers": [], "sections": [], "tables": []}
        
        with pdfplumber.open(pdf_path) as pdf:
            for page_idx, page in enumerate(pdf.pages):
                width, height = page.width, page.height
                
                # Heuristics: texts in top 10% are headers, bottom 10% are footers
                lines = page.extract_text_lines()
                for line in lines:
                    top_y = line["top"]
                    if top_y < height * 0.1:
                        layout_elements["headers"].append({"page": page_idx, "text": line["text"], "bbox": (line["x0"], line["top"], line["x1"], line["bottom"])})
                    elif top_y > height * 0.9:
                        layout_elements["footers"].append({"page": page_idx, "text": line["text"], "bbox": (line["x0"], line["top"], line["x1"], line["bottom"])})
                    else:
                        layout_elements["sections"].append({"page": page_idx, "text": line["text"], "bbox": (line["x0"], line["top"], line["x1"], line["bottom"])})
                        
        # Augment with tables
        layout_elements["tables"] = self.detect_tables_camelot(pdf_path)
        
        return layout_elements

    def _layoutparser_analysis(self, pdf_path: str) -> Dict[str, Any]:
        # Advanced functionality when model is loaded
        pass
