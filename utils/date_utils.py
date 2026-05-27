# utils/date_utils.py

from datetime import datetime, timedelta
import calendar


def parse_date(date_str, input_format="%Y-%m-%d"):
    """
    Convert string date into datetime object.
    Attempts multiple formats for robustness.
    """
    if not date_str:
        return datetime.now()
        
    formats = [input_format, "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d"]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
            
    raise ValueError(f"Time data '{date_str}' does not match any known format")


def format_date(date_obj, output_format="%d-%m-%Y"):
    """
    Convert datetime object into formatted string

    Example:
    01-02-2026
    """

    return date_obj.strftime(output_format)


def generate_audit_period(start_date_input):
    """
    Generate:
    - period_start
    - period_end

    User enters:
    2026-02-01

    Output:
    01-02-2026
    28-02-2026
    """

    start_date = parse_date(start_date_input)

    year = start_date.year
    month = start_date.month

    last_day = calendar.monthrange(year, month)[1]

    end_date = datetime(year, month, last_day)

    return {
        "period_start": format_date(start_date),
        "period_end": format_date(end_date)
    }


def generate_cash_verification_date(end_date_str):
    """
    Cash verification date:
    Usually next month +13 days

    Example:
    End Date:
    28-02-2026

    Output:
    13-03-2026
    """

    end_date = parse_date(
        end_date_str,
        "%d-%m-%Y"
    )

    verification_date = end_date + timedelta(days=13)

    return format_date(verification_date)


def generate_report_date(end_date_str):
    """
    Final report signing date

    Example:
    16 days after month end
    """

    end_date = parse_date(
        end_date_str,
        "%d-%m-%Y"
    )

    report_date = end_date + timedelta(days=16)

    return format_date(report_date)


def build_template_context(
    branch_name,
    place,
    start_date_input,
    cash_verification_date=None
):
    """
    Main utility function

    Generate all dates automatically
    for DOCX template rendering
    """

    period_data = generate_audit_period(
        start_date_input
    )

    # Use provided cash verification date or generate from period end
    if cash_verification_date:
        verification_date = cash_verification_date
    else:
        verification_date = generate_cash_verification_date(
            period_data["period_end"]
        )

    report_date = generate_report_date(
        period_data["period_end"]
    )

    context = {

        # Branch Details
        "branch_name": branch_name,
        "place": place,

        # Audit Period
        "period_start": period_data["period_start"],
        "period_end": period_data["period_end"],

        # Auto Dates
        "cash_verification_date": verification_date,
        "report_date": report_date,
    }

    return context


# TESTING
if __name__ == "__main__":

    context = build_template_context(
        branch_name="CTM",
        place="Ahmedabad",
        start_date_input="2026-02-01"
    )

    print(context)