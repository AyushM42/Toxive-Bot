def handle_response(message):
    night_strings = ["tired", "goodnight", "sleep", "late", "night", "bed", "gn"]
    split_strings = message.split()
    for ns in night_strings:
        for ss in split_strings:
            if ns in ss.lower():
                return True
    return False