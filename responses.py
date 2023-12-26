def night_response(message):
    night_strings = ["tired", "goodnight", "sleep", "late", "night", "bed", "gn", "bedtime", "midnight"]
    split_strings = message.split()
    for ss in split_strings:
        if ss.lower() in night_strings:
            return True
    return False
    
    

def league_response(message):
    league_strings = ["league"]
    split_strings = message.split()
    

def val_response(message):
    val_strings = ["val", "valorant"]
    split_strings = message.split()
    for ss in split_strings:
        if ss.lower() in val_strings:
            return True
    return False