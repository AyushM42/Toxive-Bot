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
    for ss in split_strings:
        if ss.lower() in league_strings:
            return True
    return False


def one_piece_response(message):
    league_strings = ["one piece"]
    if "one piece" in message.lower():
            return True
    return False
    

def val_response(message):
    val_strings = ["val", "valorant"]
    split_strings = message.split()
    for ss in split_strings:
        if ss.lower() in val_strings:
            return True
    return False

def kys_response(message):
    league_strings = ["kys"]
    split_strings = message.split()
    for ss in split_strings:
        if ss.lower() in league_strings:
            return True
    return False

def jjk_response(message):
    league_strings = ["jjk"]
    split_strings = message.split()
    for ss in split_strings:
        if ss.lower() in league_strings:
            return True
    if "jujutsu kaisen" in message.lower():
        return True
    return False

def toxjr_response(message):
    if message == "Junior?":
        return True