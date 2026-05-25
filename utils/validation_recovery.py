import pandas as pd
from typing import Dict, Any, Tuple
from utils.logger import logger

class ValidationEngine:
    """
    Module 16: Validation Engine
    Validates geometric/financial extraction integrity.
    """
    @staticmethod
    def validate_totals(df: pd.DataFrame, amount_col: str, total_row_index: int) -> bool:
        """
        Calculates column sum excluding the total row, checks if it equals the extracted total row value.
        """
        logger.info(f"Validating totals for column: {amount_col}")
        try:
            extracted_total = float(str(df.loc[total_row_index, amount_col]).replace(",", ""))
            # drop the total row and sum
            calc_df = df.drop(index=total_row_index)
            
            def safe_float(v):
                try:
                    return float(str(v).replace(",", ""))
                except ValueError:
                    return 0.0
                    
            calculated_sum = calc_df[amount_col].apply(safe_float).sum()
            
            # Using 1.0 margin of error for rounding
            if abs(calculated_sum - extracted_total) <= 1.0:
                return True
            else:
                logger.warning(f"Totals mismatch: calculated {calculated_sum}, extracted {extracted_total}")
                return False
        except Exception as e:
            logger.error(f"Error validating totals: {e}")
            return False
            
    @staticmethod
    def identify_duplicates(df: pd.DataFrame, key_col: str = "A/c No.") -> pd.DataFrame:
        """
        Identifies and isolates duplicate records based on account number.
        """
        if key_col in df.columns:
            duplicates = df[df.duplicated(subset=[key_col], keep=False)]
            if not duplicates.empty:
                logger.warning(f"Found {len(duplicates)} duplicate records in {key_col}")
            return duplicates
        return pd.DataFrame()


class ErrorRecoveryEngine:
    """
    Module 17: Error Recovery Engine
    Coordinates retries for fragmented parsing or OCR degradation.
    """
    def __init__(self, ocr_engine=None):
        self.ocr_engine = ocr_engine
        
    def attempt_recovery(self, extraction_failed: bool, pdf_path: str) -> Dict[str, Any]:
        """
        If standard PyMuPDF/pdfplumber layout extraction fails or misses text, 
        fallback to PaddleOCR for scanned inference on a per-page basis.
        """
        logger.info(f"Attempting recovery for {pdf_path}")
        if not extraction_failed:
            return {"status": "success", "recovered_data": None}
            
        if self.ocr_engine:
            try:
                recovered_boxes = self.ocr_engine.extract_from_pdf(pdf_path)
                return {"status": "recovered", "recovered_data": recovered_boxes}
            except Exception as e:
                logger.error(f"Recovery failed using OCR: {e}")
                return {"status": "failed", "recovered_data": None}
        else:
            logger.error("No OCR engine provided for recovery fallback.")
            return {"status": "failed", "recovered_data": None}
