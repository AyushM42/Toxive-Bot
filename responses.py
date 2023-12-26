def handle_response(message):
    night_strings = ["tired", "goodnight", "good night", "sleep", "late", "night", "bed", "gn"]
    for ns in night_strings:
        if ns in message.lower():
            return True
    return False