import json
from pathlib import Path
from typing import Dict, Any, List
from utils.logger import logger

class JSONMappingEngine:
    """
    Module 10: JSON Mapping Engine
    Handles unstructured relational data dynamically using filesystem rather than databases.
    Links Annexures, Observations, and placeholder references.
    """
    def __init__(self, json_dir: str = "extracted/json"):
        self.json_dir = Path(json_dir)
        self.json_dir.mkdir(parents=True, exist_ok=True)
        self.audit_mapping_file = self.json_dir / "audit_mapping.json"
        self._initialize_mapping()
        
    def _initialize_mapping(self):
        if not self.audit_mapping_file.exists():
            self.save_mapping({})
            
    def load_mapping(self) -> Dict[str, Any]:
        with open(self.audit_mapping_file, "r") as f:
            return json.load(f)
            
    def save_mapping(self, data: Dict[str, Any]):
        with open(self.audit_mapping_file, "w") as f:
            json.dump(data, f, indent=4)
            
    def link_observation_to_annexure(self, observation_id: str, annexure_ref: str, remarks: str, report_type: str, accounts: List[str] = None):
        """
        Maintains relationships between observations generated and the annexure reference, simulating relational state.
        """
        logger.info(f"Linking observation {observation_id} to annexure {annexure_ref}")
        data = self.load_mapping()
        
        if annexure_ref not in data:
            data[annexure_ref] = {
                "report_type": report_type,
                "observations": {}
            }
            
        data[annexure_ref]["observations"][observation_id] = {
            "remarks": remarks,
            "accounts": accounts or []
        }
        
        self.save_mapping(data)
