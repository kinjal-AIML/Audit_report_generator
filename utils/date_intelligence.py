from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from typing import Dict, Any

class DateIntelligenceEngine:
    """
    Module 14: Date Intelligence Engine
    Maintains temporal continuity across headers, filenames, and context dates.
    """
    @staticmethod
    def shift_audit_month(original_date_str: str, format_str: str = "%b %Y", months: int = 1) -> str:
        """
        Example: shift_audit_month('January 2026', '%B %Y', 1) -> 'February 2026'
        """
        try:
            dt = datetime.strptime(original_date_str, format_str)
            dt += relativedelta(months=months)
            return dt.strftime(format_str)
        except ValueError:
            return original_date_str
            
    @staticmethod
    def generate_date_context(start_date: str, end_date: str, format_str: str = "%Y-%m-%d") -> Dict[str, Any]:
        """
        Generates common date placeholders.
        """
        try:
            d_start = datetime.strptime(start_date, format_str)
            d_end = datetime.strptime(end_date, format_str)
        except ValueError:
            return {"period_start": start_date, "period_end": end_date}
            
        return {
            "period_start": d_start.strftime("%dd-%mm-%yyyy"),
            "period_end": d_end.strftime("%dd-%mm-%yyyy"),
            "audit_month": d_start.strftime("%B %Y"),
            "cash_verification_date": (d_end + timedelta(days=1)).strftime("%dd-%mm-%yyyy")
        }
