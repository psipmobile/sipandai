import re

def extract_vehicle_plate(text):
    pattern = r'\b[A-Z]{1,2} \d{1,4}(?: [A-Z]{1,3})?\b'
    
    match = re.search(pattern, text, re.IGNORECASE)
    
    if match:
        return match.group(0).upper()
    return None

def format_nopol_for_view(input_str: str) -> str:
    if not input_str or input_str.strip() == "" or "null" in input_str:
        return "Format nomor polisi tidak valid."

    groups = input_str.split(" ")

    if len(groups) == 2:
        group1 = groups[0]
        group2 = groups[1]

        alphabetic_part = ""
        numeric_part = ""

        for char in group2:
            if char.isdigit():
                numeric_part += char
            else:
                alphabetic_part += char

        return (group1.ljust(2) + alphabetic_part.ljust(3) + numeric_part.rjust(4)).upper()

    elif len(groups) == 3:
        group1 = groups[0]
        group2 = groups[1]
        group3 = groups[2]

        return (group1.ljust(2) + group3.ljust(3) + group2.rjust(4)).upper()

    elif len(groups) > 3:
        group1 = groups[0]
        group2 = groups[1]
        group3 = groups[-1]

        return (group1.ljust(2) + group3.ljust(3) + group2.rjust(4)).upper()

    else:
        return "Format nomor polisi tidak valid."
