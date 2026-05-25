from typing import Dict, Any, List
from utils.logger import logger

class AIObservationEngine:
    """
    Module 11: AI Observation Engine
    Generates observation descriptions and audit summaries without altering financial data.
    """
    def __init__(self):
        pass
        
    def generate_npa_observation(self, npa_accounts_count: int, total_amount: float) -> str:
        logger.info(f"Generating NPA observation structure for {npa_accounts_count} accounts")
        if npa_accounts_count == 0:
            return "No NPA accounts were identified during this audit period."
        
        return (f"During the concurrent audit, we identified {npa_accounts_count} accounts "
                f"which have transitioned or remained in NPA status. The aggregate amount "
                f"involved is INR {total_amount:,.2f}. Details correspond to Annexure-2.")
        
    def generate_insurance_observation(self, expired_policies: int) -> str:
        logger.info(f"Generating Insurance observation structure for {expired_policies} policies")
        if expired_policies == 0:
            return "All verified loan accounts possess active and adequately renewed insurance policies."
            
        return (f"We observed {expired_policies} instances where property/stock insurance "
                f"policies attached to credit facilities have expired and remain unrenewed. "
                f"The branch must ensure prompt renewal to mitigate compliance risk as detailed in Annexure-1.")

    def compile_anomalies(self, json_mapping: Dict[str, Any]) -> Dict[str, str]:
        """
        Compiles anomaly textual payloads to be injected into docx templates.
        """
        placeholders = {}
        for annexure_ref, data in json_mapping.items():
            report_type = data.get("report_type", "General")
            obs_dict = data.get("observations", {})
            obs_count = len(obs_dict)
            
            if report_type.lower() == "npa":
                placeholders["npa_observation"] = self.generate_npa_observation(obs_count, 0.0) # Amounts injected differently
            elif report_type.lower() == "insurance":
                placeholders["insurance_annexure"] = self.generate_insurance_observation(obs_count)
                
        return placeholders
