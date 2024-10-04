def night_response(message):
    night_strings = ["tired", "goodnight", "sleep", "late", "night", "bed", "gn", "bedtime", "midnight", "sleepy", "tonight"]
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

def bankai_response(message):
    league_strings = ["bankai", "https://tenor.com/view/bleach-bankai-court-young-thug-thug-gif-7984140487879273755", "https://tenor.com/view/me-showing-the-class-my-bankai-gif-580868976631931335"]
    if "bankai" in message.lower():
        return True
    split_strings = message.split()
    for ss in split_strings:
        if ss.lower() in league_strings:
            return True
    return False

def honkai_response(message):
    league_strings = ["honkai", "starrail"]
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

def bubblesort_response(message):
    if ("bubble sort" in message.lower()) or ("buble sort" in message.lower()):
            return True
    return False
    

def val_response(message):
    val_strings = ["val", "valorant"]
    split_strings = message.split()
    for ss in split_strings:
        if ss.lower() in val_strings:
            return True
    return False

def fortnite_respons(message):
    val_strings = ["fortnite", "fort"]
    split_strings = message.split()
    for ss in split_strings:
        if ss.lower() in val_strings:
            return True
    return False

def kys_response(message):
    league_strings = ["kys", "kms"]
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
    
def joever_response(message):
    if "joever" in message.lower():
        return True
    
def hi_response(message):
    message = message.lower()
    if message[0:2] == "hi" and message.split()[0][2:].strip("i").strip() == "":
        return 1
    if message[0:2] == "ha" and message.split()[0][2:].strip("i").strip() == "":
        return 2
