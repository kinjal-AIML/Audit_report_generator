import pandas as pd
import os

def generate_master_excel(data_dict, output_dir):
    """
    Creates MASTER_AUDIT_DATA.xlsx with multiple sheets.
    data_dict: { 'Sheet Name': df, ... }
    """
    output_path = os.path.join(output_dir, "MASTER_AUDIT_DATA.xlsx")
    
    # Pre-defined mandatory sheets to ensure they appear first
    priority_sheets = [
        "Audit Summary",
        "Audit Observations",
        "Annexures"
    ]
    
    all_sheet_names = priority_sheets + [k for k in data_dict.keys() if k not in priority_sheets]
    
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        for sheet_name in all_sheet_names:
            # Get data from dict or create empty placeholder for priority sheets
            df = data_dict.get(sheet_name)
            
            if df is None:
                if sheet_name in priority_sheets:
                    df = pd.DataFrame(columns=["Details", "Remarks", "Annexure Ref"])
                else:
                    continue
            
            # Final column sanitization for Excel
            if "Remarks" not in df.columns:
                df["Remarks"] = ""
            if "Annexure Ref" not in df.columns:
                df["Annexure Ref"] = ""
                
            # Limit sheet name length for Excel (max 31 chars)
            safe_sheet_name = sheet_name[:31]
            df.to_excel(writer, sheet_name=safe_sheet_name, index=False)
            
    return output_path

def generate_annexure_workbook(data_dict, output_dir):
    """
    Creates separate Annexure Workbook if needed (Step 10).
    """
    output_path = os.path.join(output_dir, "ANNEXURE_WORKBOOK.xlsx")
    # Implementation similar to master excel but specifically for annexures
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        df_annexures = data_dict.get("Annexures", pd.DataFrame())
        df_annexures.to_excel(writer, sheet_name="Annexures", index=False)
    return output_path
