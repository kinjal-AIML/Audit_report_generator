def number_to_indian_rupees(amount_str):
    """
    Convert a numeric amount to Indian Rupees words format.
    
    Examples:
    - "1002738" -> "Ten Lakh Two Thousand Seven Hundred Thirty Eight Rupees Only"
    - "1234.56" -> "One Thousand Two Hundred Thirty Four Rupees Fifty Six Paise Only"
    """
    
    # Clean and parse the amount
    amount_str = str(amount_str).replace(',', '').strip()
    
    if '.' in amount_str:
        parts = amount_str.split('.')
        whole_part = parts[0]
        decimal_part = parts[1].ljust(2, '0')[:2]  # Take up to 2 decimal digits
    else:
        whole_part = amount_str
        decimal_part = "00"
    
    # Convert whole number to words in Indian format
    whole_words = _convert_whole_indian(int(whole_part)) if whole_part else "Zero"
    
    # Build the result
    result = f"{whole_words} Rupees"
    
    if int(decimal_part) > 0:
        paise_words = _convert_whole_indian(int(decimal_part))
        result = f"{whole_words} Rupees {paise_words} Paise"
    
    result += " Only"
    return result


def _convert_whole_indian(n):
    """
    Convert a whole number to Indian numbering system words.
    Indian system: Ones, Tens, Hundreds, Thousands, Ten Thousands, Lakhs, Ten Lakhs, Crores
    """
    if n == 0:
        return "Zero"
    
    ones = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", "Ten",
            "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen", "Seventeen",
            "Eighteen", "Nineteen"]
    
    twenties = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]
    
    def convert_below_1000(num):
        if num < 20:
            return ones[num]
        elif num < 100:
            return twenties[num // 10] + (" " + ones[num % 10] if num % 10 else "")
        else:
            return ones[num // 100] + " Hundred" + (" " + convert_below_1000(num % 100) if num % 100 else "")
    
    # Indian denominations
    denominations = ["", "Thousand", "Lakh", "Crore"]
    
    # Split into groups: Hundreds, Thousands, Lakhs (in pairs)
    # For Indian system: we split as ... Crore, Lakhs (2 digits), Thousands (2 digits), Hundreds
    # Handle large numbers
    crore = n // 10000000
    n %= 10000000
    
    lakh = n // 100000
    n %= 100000
    
    thousand = n // 1000
    n %= 1000
    
    hundred = n
    
    parts = []
    if crore > 0:
        parts.append(convert_below_1000(crore) + " Crore")
    if lakh > 0:
        parts.append(convert_below_1000(lakh) + " Lakh")
    if thousand > 0:
        parts.append(convert_below_1000(thousand) + " Thousand")
    if hundred > 0:
        parts.append(convert_below_1000(hundred))
    
    result = " ".join(parts).strip()
    # Clean up extra spaces
    result = " ".join(result.split())
    return result


if __name__ == "__main__":
    # Test cases
    print(number_to_indian_rupees("1002738"))
    print(number_to_indian_rupees("1002738.00"))
    print(number_to_indian_rupees("1234.56"))
    print(number_to_indian_rupees("50000"))