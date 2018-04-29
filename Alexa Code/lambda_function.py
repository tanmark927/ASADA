# To use this
# send { "type": "FortuneCookie" }
def fortune_cookie():
    return { "cookie": "Heliijulo, world" }

# --------------- Main handler ------------------

def lambda_handler(event, context):
    print("Harry:")
    print("event:")
    print(event)
    if event["type"] == "FortuneCookie":
        return fortune_cookie()