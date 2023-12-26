def handle_response(message):
    night_strings = ["tired", "goodnight", "sleep", "late", "night", "bed", "gn"]
    split_strings = message.split()
    for ss in split_strings:
        if ss.lower() in night_strings:
            return True
    return False