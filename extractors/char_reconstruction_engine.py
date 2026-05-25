import pdfplumber
from typing import List, Tuple, Dict
from utils.logger import logger

class CharacterReconstructionEngine:
    """
    Module 3: Character-Level Word Reconstruction Engine
    Solves the problem of micro-gaps inside words and larger gaps between words in ERP banking PDFs.
    """
    def __init__(self, intra_word_gap: float = 3.0, inter_word_gap: float = 15.0, y_tolerance: float = 3.0):
        self.INTRA_WORD_GAP_PX = intra_word_gap
        self.INTER_WORD_GAP_PX = inter_word_gap
        self.Y_TOLERANCE = y_tolerance

    def chars_to_words(self, chars: List[Dict]) -> List[Tuple[float, float, str]]:
        """
        Groups characters into distinct word tokens utilizing dynamic gap thresholding.
        Returns: list of (x0, x1, text).
        """
        if not chars:
            return []
        
        # Sort characters by x-coordinate to correctly reconstruct left-to-right
        chars_sorted = sorted(chars, key=lambda c: c["x0"])
        tokens = []
        buf = [chars_sorted[0]]

        for c in chars_sorted[1:]:
            gap = c["x0"] - buf[-1]["x1"]
            if gap <= self.INTRA_WORD_GAP_PX:
                buf.append(c)
            else:
                tokens.append((buf[0]["x0"], buf[-1]["x1"], "".join(ch["text"] for ch in buf)))
                buf = [c]
        
        # Flush final buffer
        tokens.append((buf[0]["x0"], buf[-1]["x1"], "".join(ch["text"] for ch in buf)))
        return tokens

    def extract_page_rows(self, page) -> List[Tuple[float, List[Tuple[float, float, str]]]]:
        """
        Returns ordered list of rows from a pdfplumber page.
        Groups characters by y-position (top) before word reconstruction.
        """
        chars = [c for c in page.chars if c.get("text", "").strip()]
        row_map = {}
        for c in chars:
            key = round(c["top"] / self.Y_TOLERANCE) * self.Y_TOLERANCE
            row_map.setdefault(key, []).append(c)

        rows = []
        for top in sorted(row_map):
            tokens = self.chars_to_words(row_map[top])
            if tokens:
                rows.append((top, tokens))
        return rows

    def extract_all_rows_multipage(self, pdf_path: str) -> List[Tuple[int, float, List[Tuple[float, float, str]]]]:
        """
        Returns a flat list of (page_index, y_coord, tokens) across the entire document.
        """
        logger.info(f"Reconstructing characters and grouping rows for {pdf_path}")
        result = []
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for pi, page in enumerate(pdf.pages):
                    for top, tokens in self.extract_page_rows(page):
                        result.append((pi, top, tokens))
        except Exception as e:
            logger.error(f"Error reading PDF {pdf_path}: {e}")
        return result
