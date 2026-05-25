from typing import List, Tuple, Dict, Any
import re
from utils.logger import logger

class SemanticRowReconstructionEngine:
    """
    Module 5: Semantic Row Reconstruction Engine
    Groups visual rows that form a single logical financial record.
    """
    def __init__(self):
        # We define a new logical block when we see a 6-digit account number as the first token
        self.ACCOUNT_NUMBER_PATTERN = re.compile(r"^\d{6}$")
        self.SUMMARY_PATTERN = re.compile(r"^(Typewise|Branchwise|Grand|Total)", re.IGNORECASE)
        self.NOISE_PATTERN = re.compile(
            r"THE MEHSANA|PANCHOT BRANCH|MICR:-|IFSC:-|Print Date|"
            r"^-{5,}$|User Name:|Page \d+ of|^Clerk\s|^Cashier\s|"
            r"Security Details|A/c No\.\s+Name\s+NPA|"
            r"Overdue Report For All|Cash Summary Report|Insurance Pending Register",
            re.IGNORECASE
        )

    def is_noise(self, text: str) -> bool:
        return bool(self.NOISE_PATTERN.search(text))

    def reconstruct_logical_records(self, token_rows: List[Tuple[int, float, List[Tuple[float, float, str]]]]) -> List[Dict[str, Any]]:
        """
        Takes raw char-clustered token rows from Module 3 and reconstructed blocks.
        Each block groups the primary row and connected secondary rows spanning multiple vertical lines.
        Returns a list of reconstructed logical blocks.
        """
        logger.info("Reconstructing logical semantic rows")
        blocks = []
        current_block = {}
        
        for page_idx, y_coord, tokens in token_rows:
            if not tokens:
                continue
                
            line_text = " ".join(t[2] for t in tokens)
            if self.is_noise(line_text):
                continue
            
            first_tok = tokens[0][2]
            
            is_new_record = self.ACCOUNT_NUMBER_PATTERN.match(first_tok)
            is_summary_record = self.SUMMARY_PATTERN.match(first_tok)
            
            if is_new_record or is_summary_record:
                if current_block:
                    blocks.append(current_block)
                current_block = {
                    "primary_row": {"page": page_idx, "y_coord": y_coord, "tokens": tokens},
                    "secondary_rows": [],
                    "record_type": "ACCOUNT" if is_new_record else "SUMMARY"
                }
            else:
                # If it's not a new record start, it must belong to the existing block as a continuation
                if current_block:
                    current_block["secondary_rows"].append({
                        "page": page_idx, "y_coord": y_coord, "tokens": tokens
                    })
                else:
                    # Header/Branch definitions outside blocks
                    pass

        # Flush final block
        if current_block:
            blocks.append(current_block)
            
        logger.debug(f"Reconstructed {len(blocks)} semantic blocks")
        return blocks
