from __future__ import print_function
import sys
import logging
import pymysql
import datetime
import math
import string
import random
import uuid
import geocoder
import requests
import json
from datetime import date

#rds settings
rds_host  = "asada.cofr9vg9xjlm.us-east-1.rds.amazonaws.com"
name = "asadadepression"
password = "Dontbesad1"
db_name = "asadaDB"

#-------variables for survey-------

OPENING_MESSAGE = "This is the Patient Health Questionnaire. " \
                   "It will measure the status of your well-being. " \
                   "You can answer by saying never, sometimes, often or always. "

SKILL_TITLE = "Patient Health Questionnaire"
BEGIN_STATEMENT = "You will be asked 9 questions about recent problems you have faced. "
END_STATEMENT = "Thank you for completing the Patient Health Questionnaire. "

USE_CARDS_FLAG = False

LAST_SPOKEN = ""
USER_IDENTIFICATION = 2222
USER_WELL_BEING = 0

STATE_START = "Start"
STATE_SURVEY = "Questionnaire"

STATE = STATE_START
COUNTER = 0
QUIZSCORE = 0

SAYAS_INTERJECT = "<say-as interpret-as='interjection'>"
SAYAS_SPELLOUT = "<say-as interpret-as='spell-out'>"
SAYAS = "</say-as>"
BREAKSTRONG = "<break strength='strong'/>"

logger = logging.getLogger()
logger.setLevel(logging.INFO)

try:
    conn = pymysql.connect(rds_host, user=name, passwd=password, db=db_name, connect_timeout=5)
except:
    logger.error("ERROR: Unexpected error: Could not connect to MySql instance.")
    sys.exit()

logger.info("SUCCESS: Connection to RDS mysql instance succeeded")


# --------------- Helpers that build all of the responses ----------------------

#this writes out the conversation date that the user has the ASADA with the messages that are sent and date of messages
def write_to_conversation(userID, outgoing, message):
    
    with conn.cursor() as cursor:
        now = datetime.datetime.now()
        date = now.strftime("%Y-%m-%d")
        print(message)
        sql = "INSERT INTO Conversation (UserID, outgoing, dateSent, message) VALUES ({0}, {1}, '{2}', '{3}');".format(userID, outgoing, date, message)
        cursor.execute(sql)
    conn.commit()

#regular speechlet response builder for Alexa Skill Kit
def build_speechlet_response(title, output, reprompt_text, should_end_session):
    return {
        'outputSpeech': {
            'type': 'PlainText',
            'text': output
        },
        'card': {
            'type': 'Simple',
            'title': title,
            'content':  output
        },
        'reprompt': {
            'outputSpeech': {
                'type': 'PlainText',
                'text': reprompt_text
            }
        },
        'shouldEndSession': should_end_session
    }
#fetching permission json card builder for Alexa Skills Kit
def build_permission_response(output, reprompt_text, should_end_session):
    return {
        'outputSpeech': {
            'type': 'PlainText',
            'text': output
        },
         'card': {
            'type': 'AskForPermissionsConsent',
            'title': 'Permission Request',
            'permissions': ['read::alexa:device:all:address'],
            'content': output
        },
        'reprompt': {
            'outputSpeech': {
                'type': 'PlainText',
                'text': reprompt_text
            }
        },
        'shouldEndSession': should_end_session
    }


#builds the speech response that Alexa outputs 
def build_response(session_attributes, speechlet_response):
    return {
        'version': '1.0',
        'sessionAttributes': session_attributes,
        'response': speechlet_response
    }

#depression survey function
ITEMS = []
ITEMS.append("How often do you feel little interest or pleasure in doing things?")
ITEMS.append("How often do you feel down, depressed or hopeless?")
ITEMS.append("How often do you have trouble falling asleep, staying asleep, or sleeping too much?")
ITEMS.append("How often do you feel tired or have little energy for activities?")
ITEMS.append("How often are you bothered with a poor appetite or overeating?")
ITEMS.append("How often do you have bad thoughts about yourself?")
ITEMS.append("How often have you had trouble concentrating on an activity?")
ITEMS.append("How often are you bothered with moving and speaking slowly or feeling fidgety and restless?")
ITEMS.append("How often have you had thoughts of hurting yourself in some way?")

# --------------- Functions that control the skill's behavior ------------------

#user gets a response from ASADA when first starting up the system with info on what they can say or ask for help
def get_welcome_response():
    card_title = "Welcome"
    speech_output = "Welcome to ASADA. " \
                    "If you need help, try saying, " \
                    "ASADA help, for help talking to me"
    reprompt_text = "Again, try saying, ASADA help, if you need additional assistance"
    session_attributes = {
        'lastSpoken' : speech_output
    }
    should_end_session = False
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

#handles when the user wants to exit the ASADA program so ASADA outputs a 'goodbye' speech response once the user finishes using ASADA
def handle_session_end_request():
    card_title = "Session Ended"
    speech_output = "Thank you for using ASADA. " \
                    "Have a nice day! "
    
    should_end_session = True
    return build_response({}, build_speechlet_response(
        card_title, speech_output, None, should_end_session))

# --------------- Events ------------------

#calls out when the user session started with Alexa
def on_session_started(session_started_request, session):
    """ Called when the session starts """
    print("on_session_started requestId=" + session_started_request['requestId']
          + ", sessionId=" + session['sessionId'])

#a skill is called on but unspecified so the welcome response runs and Alexa prompts the user to ask for help
def on_launch(launch_request, session):
    """ Called when the user launches the skill without specifying what they
    want
    """
    print("on_launch requestId=" + launch_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # Dispatch to your skill's launch
    return get_welcome_response()

#Convert actual quiz score to overall well-being
def calculate_well_being(score):
    if (score >= 0 and score <= 4):
        return 5;
    elif (score >= 5 and score <= 9):
        return 4;
    elif (score >= 10 and score <= 14):
        return 3;
    elif (score >= 15 and score <= 20):
        return 2;
    elif score > 20:
        return 1;

'''
Calling this function returns a statement of a list of tasks to try out
'''
def help_asada():
    global USER_IDENTIFICATION
    card_title = "help function"
    speech_output = "You can request a well being survey, ask for general advice, " \
                    "ask specific advice like eating, sleeping and exercise, find a local therapist, " \
                    "or hear a random motivational quote. You will also receive advice " \
                    "in the case that I hear a statement of self harm."
    reprompt_text = "I did not understand your command. " \
                    "Try saying, ASADA help, for help talking to me"
    should_end_session = False
    session_attributes = {
        'lastSpoken' : speech_output
    }
    write_to_conversation(USER_IDENTIFICATION, 0, speech_output)
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))
        
'''
Allows you to repeat what was last spoken by ASADA
'''
def repeat_command(session):
    global LAST_SPOKEN    

    card_title = ""
    session_attributes = {}
    speech_output = ""
    reprompt_text = ""
    if not( session['attributes']['lastSpoken'] is None):
        speech_output = session['attributes']['lastSpoken']
        reprompt_text = speech_output
        globals()['LAST_SPOKEN'] = speech_output
        should_end_session = False
        session_attributes = {
            'lastSpoken' : globals()['LAST_SPOKEN']
        }
    if (session['attributes']['state'] == STATE_SURVEY):
        session_attributes = {
                "quizscore":session['attributes']['quizscore'],
                "quizproperty":session['attributes']['quizproperty'],
                "response":session['attributes']['response'],
                'lastSpoken' : speech_output,
                "state": session['attributes']['state'],
                "counter": session['attributes']['counter'],
        }
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))
    
#Recommend phone numbers that can help the user with serious issues    
def death_alert():
    global USER_IDENTIFICATION
    card_title = "911 emergency function"
    speech_output = "I recommend you call 911 or the suicide hotline 1 800 273 8255"
    reprompt_text = "I did not understand your command. " \
                    "Try saying, ASADA help, for help talking to me"
    should_end_session = False
    session_attributes = {
        'lastSpoken' : speech_output
    }
    write_to_conversation(USER_IDENTIFICATION, 0, speech_output)
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

'''
When someone says thank you say you are welcome!
'''
def give_thanks():
    global USER_IDENTIFICATION
    card_title = "Give Thanks"
    speech_output = "You are welcome."
    reprompt_text = "I am sorry I did not understand" \
                    "Try saying, ASADA help, for help talking to me"
    should_end_session = False
    session_attributes = {
        'lastSpoken' : speech_output
    }
    write_to_conversation(USER_IDENTIFICATION, 0, speech_output)
    return build_response(session_attributes, build_speechlet_response(
                card_title, speech_output, reprompt_text, should_end_session))    

'''
Returns a random fortune for you
'''
def fortune_cookie():
    global USER_IDENTIFICATION
    card_title = "Fortune Cookie"
    result = ""
    with conn.cursor() as cur:
        cur.execute("select FC_Message from FortuneCookie ORDER BY RAND() LIMIT 1")
        result = cur.fetchone()
        speech_output = result[0]
        reprompt_text = "I did not understand your command. " \
                    "Try saying, ASADA help, for help talking to me"
        should_end_session = False
        session_attributes = {
            'lastSpoken' : speech_output
        }
        write_to_conversation(USER_IDENTIFICATION, 0, speech_output)
        return build_response(session_attributes, build_speechlet_response(
                card_title, speech_output, reprompt_text, should_end_session))
 
#Allows a user to create an account for ASADA
def createAnAccount(intent):
    global USER_IDENTIFICATION
    card_title = "Create An Account"
    u_name =  intent['slots']['FirstName']['value']

    with conn.cursor() as cur:
        try:
            #Check if username already exists in the database
            cur.execute("select UserID from Users where UserName = %s LIMIT 1", [u_name])
            result = cur.fetchone()
            
            #Generate random number for the user ID
            id = str(random.randint(1, 1000))

            if(type(result) is not type(None)):
                speech_output = "User already exists."
            else:
                #Insert new user info into database
                cur.execute("INSERT into Users (UserID, UserName) VALUES('{0}', '{1}')".format(id, u_name))
                USER_IDENTIFICATION = int(u_name)
                speech_output = "You have sucessfully created an account"
        except ValueError:
            #Prompt user to restate one's name
            speech_output = "Please restate your name."
    #Prompt user to restate one's name    
    reprompt_text = "Please restate your name."
    should_end_session = False
    session_attributes = {
        'lastSpoken' : speech_output
    }
    write_to_conversation(USER_IDENTIFICATION, 0, speech_output)
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

#Allows user to sign into ASADA
def user_intro(intent):
    global USER_IDENTIFICATION
    global QUIZSCORE
    card_title = "User Introduction"

    #Retrieve username from user's last response
    u_name =  intent['slots']['FirstName']['value']

    with conn.cursor() as cur:
        try:
            #Check if user already exists in the database
            cur.execute("select UserID from Users where UserName = %s LIMIT 1", [u_name])
            result = cur.fetchone()
            
            #Assign user ID to global variable if it exists
            if type(result) is not type(None):
                USER_IDENTIFICATION = result[0]
            
            #Check if user has taken a survey
            cur.execute("select SurveyScore from Survey where UserID = %s order by SurveyDate desc limit 1", [USER_IDENTIFICATION])
            result_two = cur.fetchone()

            #Assign user's recent survey score to global variable if it exists
            if type(result_two) is not type(None):
                QUIZSCORE = result_two[0]
            
            if(type(result) is not type(None) and type(result_two) is not type(None)):
                #User has an account and has taken a survey
                speech_output = "Welcome " + u_name + " to ASADA."
            elif(type(result) is not type(None) and type(result_two) is type(None)):
                #User has an account and has not taken a survey
                speech_output = "Welcome " + u_name + " to ASADA. Please take a survey so that I can better target your needs."
            else:
                #User has yet to make an account
                speech_output = "Please register your name."
        except ValueError:
            speech_output = "Excuse me but who are you?"
        
    reprompt_text = "Excuse me but who are you? Please restate your name"
    should_end_session = False
    session_attributes = {
        'lastSpoken' : speech_output
    }
    write_to_conversation(USER_IDENTIFICATION, 0, speech_output)
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

#Retrieve a piece of exercise advice depending on a user's well-being
def exercise_habits():
    global USER_IDENTIFICATION
    global QUIZSCORE
    card_title = "Exercise Habits"
    result = ""
    exercise_intensity = 0
    with conn.cursor() as cur:
        #Get most recent user input
        cur.execute("select * from Conversation order by conversationID desc limit 1;")
        first_result = cur.fetchone()
        well_being = calculate_well_being(globals()['QUIZSCORE'])

        #Retrieve advice based on user input and user intensity
        if 'arms' in first_result:
            cur.execute("select FA_Description from FitnessActivity where FA_Category = 'arms' and FA_Intensity = %s ORDER BY RAND() LIMIT 1", [well_being])
            result = cur.fetchone()
        elif 'legs' in first_result:
            cur.execute("select FA_Description from FitnessActivity where FA_Category = 'legs' and FA_Intensity = %s ORDER BY RAND() LIMIT 1", [well_being])
            result = cur.fetchone()
        elif 'chest' in first_result:
            cur.execute("select FA_Description from FitnessActivity where FA_Category = 'chest' and FA_Intensity = %s ORDER BY RAND() LIMIT 1", [well_being])
            result = cur.fetchone()
        elif 'back' in first_result:
            cur.execute("select FA_Description from FitnessActivity where FA_Category = 'back' and FA_Intensity = %s ORDER BY RAND() LIMIT 1", [well_being])
            result = cur.fetchone()
        else:
            #execute this query if user command does not specify area of exercise
            cur.execute("select FA_Description from FitnessActivity ORDER BY RAND() LIMIT 1")
            result = cur.fetchone()
            
        speech_output = result[0]
        reprompt_text = ""
        should_end_session = False
        session_attributes = {
            'lastSpoken' : speech_output
        }
        write_to_conversation(USER_IDENTIFICATION, 0, speech_output)
        return build_response(session_attributes, build_speechlet_response(
                card_title, speech_output, reprompt_text, should_end_session))

#Convert well-being score into severity for advice
def severity_calculator(well_being_score):
    if well_being_score == 5:
        return 1
    elif well_being_score == 4:
        return 2
    elif well_being_score == 3:
        return 3
    elif well_being_score == 2:
        return 4
    elif well_being_score == 1:
        return 5

def specific_habits(intent_name):
    global USER_IDENTIFICATION
    global QUIZSCORE
    card_title = ""
    query = ""
    
    #Change card title and query depending on intent parameter
    if intent_name == "SleepHabits":
        card_title = "Sleep Habits"
        query = "select advice from SleepAdvice where severity = %s ORDER BY RAND() LIMIT 1"
    elif intent_name == "EatingHabits":
        card_title = "Eating Habits"
        query = "select advice from EatingAdvice where severity = %s ORDER BY RAND() LIMIT 1"
    
    #Convert quiz score to severity
    well_being = calculate_well_being(globals()['QUIZSCORE'])
    severity = severity_calculator(well_being)
    
    #Retrieve a random piece of specific advice
    with conn.cursor() as cur:
        cur.execute(query, [severity])
        result = cur.fetchone()
        speech_output = result[0]
        reprompt_text = "I did not understand your command. " \
                    "Try saying, ASADA help, for help talking to me"
        should_end_session = False
        session_attributes = {
            'lastSpoken' : speech_output
        }
        write_to_conversation(USER_IDENTIFICATION, 0, speech_output)
        return build_response(session_attributes, build_speechlet_response(
            card_title, speech_output, reprompt_text, should_end_session))

#Notifies the user about changes in survey scores
def survey_tracker():
    global USER_IDENTIFICATION
    card_title = "Survey Tracker"
    with conn.cursor() as cur:
        
        #get most recent survey result
        cur.execute("select SurveyScore from Survey where UserID = %s order by SurveyDate desc limit 1", [USER_IDENTIFICATION])
        result_A = cur.fetchone()
        new_s_res = result_A[0]
        
        #get survey result from last week
        cur.execute("select SurveyScore from Survey where UserID = %s and SurveyDate = DATE_SUB(CURDATE(), INTERVAL 7 DAY) order by SurveyDate desc limit 1",[USER_IDENTIFICATION])
        result_B = cur.fetchone()
        old_s_res = result_B[0]
        
        if type(result_A) is type(None) and type(result_B) is type(None):
            #new and old results are empty
            speech_output = "For the survey tracker to function, you need to take surveys " \
                            "over the course of a few weeks to see progress."
        elif type(result_A) is not type(None) and type(result_B) is type(None):
            #old result is empty but new result is not
            speech_output = "For the survey tracker to function, you need to take one more " \
                            "survey in the next few days to see progress."
        elif type(result_A) is not type(None) and type(result_B) is not type(None):
            #both results are filled
            score_diff = float(new_s_res) - float(old_s_res)
            if score_diff == 0:
                speech_output = "There has been no change in your well-being since last week."
            if score_diff > 0:
                #well-being has reduced
                if abs(score_diff) > 5:
                    speech_output = "There has been a major negative change in your well-being since last week."
                else:
                    speech_output = "There has been a minor negative change in your well-being since last week."
            elif score_diff < 0:
                #well-being has increased
                if abs(score_diff) > 5:
                    speech_output = "There has been a major positive change in your well-being since last week."
                else:
                    speech_output = "There has been a minor positive change in your well-being since last week."
        
        reprompt_text = "I did not understand your command. " \
                    "Try saying, ASADA help, for help talking to me"
        should_end_session = False
        session_attributes = {
            'lastSpoken' : speech_output
        }
        write_to_conversation(USER_IDENTIFICATION, 0, speech_output)
        return build_response(session_attributes, build_speechlet_response(
            card_title, speech_output, reprompt_text, should_end_session))


#-----------------------Quiz function---------------#

#returns the question for the survey
def ask_question(request, speech_output):
    global QUIZSCORE
    global COUNTER
    global STATE
    #reset COUNTER
    if globals()['COUNTER'] <= 0:
        globals()['COUNTER'] = 0
        speech_output += OPENING_MESSAGE
    
    globals()['COUNTER'] += 1
    #fetch question from table depending on the counter of the survey
    quiz_question = str(ITEMS[COUNTER - 1])
    speech_output += quiz_question
    card_title = "Question" + str(COUNTER)
    #creates the session attributes for the survey
    session_attributes = {"quizscore":globals()['QUIZSCORE'],
                  "quizproperty":quiz_question,
                  "response":speech_output,
                  'lastSpoken' : speech_output,
                  "state": globals()['STATE'],
                  "counter":globals()['COUNTER'],
                 }
  
    reprompt_text = "I did not understand your command. " \
                    "Try saying, ASADA help, for help talking to me"
    should_end_session = False
    return build_response(session_attributes, build_speechlet_response(
    	card_title, speech_output, reprompt_text, should_end_session))    

#starts the survey, sets the global variables to set into the session attributes
def do_quiz(request):
    global QUIZSCORE
    global COUNTER
    global STATE
    
    COUNTER = 0
    QUIZSCORE = 0
    STATE = STATE_SURVEY
    return ask_question(request, "")

#pre-process the answer, checks if the user is in the survey state.
#returns a question if the user is in the state
#returns a statement saying the user is not in the state
def answer(request, intent, session, context):
    global STATE
    
    if STATE == STATE_SURVEY:
        return answer_quiz(request, intent, session, context)
    session_attributes = {}
    speech_output = "You are not in the Depression screening process at the moment. You can say take the survey or start the survey"
    card_title = "Gave survey answers while not in survey process"
    should_end_session = False
    reprompt_text = "I did not understand your command. "
    session_attributes = {
        'lastSpoken' : speech_output
    }
    return build_response(session_attributes, build_speechlet_response(
                card_title, speech_output, reprompt_text, should_end_session))

#processes the survey score, depending on the response.
def answer_quiz(request, intent, session, context):
    global QUIZSCORE
    global COUNTER
    global STATE
    global USER_IDENTIFICATION

    speech_message = ""
    quiz_question = ""
    
    #check if first question, and put welcome message?
    #processes the user's answers, getting the id of the response.
    if session['attributes'] and session['attributes']['quizscore'] != None:
        QUIZSCORE = session['attributes']['quizscore']
    if 'Answer' in intent['slots']:
        QUIZSCORE += int(intent['slots']['Answer']['resolutions']['resolutionsPerAuthority'][0]['values'][0]['value']['id'])
        
    if COUNTER < len(ITEMS):
        return ask_question(request, "")
    speech_message += get_result(QUIZSCORE)
    
    #saves to database
    with conn.cursor() as cursor:
        surveyID = uuid.uuid4()
        now = date.today()
        sql = "INSERT INTO Survey (SurveyID, SurveyDate, SurveyScore, UserID) VALUES ('{0}', '{1}', '{2}', {3});".format(surveyID, now, QUIZSCORE, USER_IDENTIFICATION)
        cursor.execute(sql)
    conn.commit()
    
    STATE = STATE_START
    COUNTER = 0
    QUIZSCORE = 0
    
    session_attributes = {"quizscore":globals()['QUIZSCORE'],
                  "quizproperty":quiz_question,
                  "response":speech_message,
                  "state": globals()['STATE'],
                  "counter":globals()['COUNTER']
                 }
    reprompt_text = ""
    should_end_session = False
    card_title = "Survey"
    return build_response(session_attributes, build_speechlet_response(
                card_title, speech_message, reprompt_text, should_end_session))
    
#returns the results, consulting on how many times the user should use ASADA    
def get_result(score):
    if(score >= 0 and score <= 4):
        return "based on your screening, you should consult with ASADA at least once every two weeks."
    elif(score >= 5 and score <= 9):
        return "based on your screening, you should consult with ASADA at least once every few days. It is recommended to take the survey every two weeks."
    elif(score >= 10 and score <= 14):
        return "based on your screening, you should consult with ASADA at least once a day. It is recommended to take the survey every two weeks."
    elif(score >= 15 and score <= 20):
        return "based on your screening, you should consult with ASADA once a day." \
        "It is recommended to seek professional help. It is recommended to take the survey every two weeks."
    elif(score > 20):
        return "based on your screening, you should consult a therapist about your recent experiences and take the survey once a week. We recommend you use the Find Therapist feature of ASADA."

#finds a therapist depending on the user's address. 
#finds the nearest therapist, depending on the user's device address inside. 
#returns a permission request if the user have not given permission
def find_therapist(context):
    #global SURVEY_THERAPIST
    deviceId = context['context']['System']['device']['deviceId']
    print(deviceId)
    """This functions gets the location of the User's Alexa device, if they have granted location permissions. """
    URL = "https://api.amazonalexa.com/v1/devices/{}/settings/address".format(deviceId)
    TOKEN = context['context']['System']['apiAccessToken']
    HEADER = {'Accept': "application/json",'Authorization': "Bearer {}".format(TOKEN)}
    print(HEADER)
    print(TOKEN)
    print(URL)
    #requests the user address from Alexa skills
    r = requests.get(URL, headers=HEADER)
    print(r.status_code)
    if(r.status_code == 200):
        #fetches the response as a json
        alexa_location = r.json()
        print("aaaaa",alexa_location)
        #the address taken from the json
        address = "{} {}".format(alexa_location["addressLine1"],
                             alexa_location["city"])
    #checks status code
    if(r.status_code == 403):
        speech_output = "Please go to the Alexa app on your smartphone, and allow the permissions for this skill to request your address"
        reprompt_text = "Please go to the Alexa app on your smartphone, and allow the permissions for this skill to request your address"
        should_end_session = False;
        session_attributes = {
            'lastSpoken' : speech_output
        }
        return build_response(session_attributes, build_permission_response(speech_output, reprompt_text, should_end_session))
    keyword = "(therapist OR psychiatrist) AND MD"
    #finds the lattitude and longitude of the user's address
    g = geocoder.google(address, key='AIzaSyA-xvMIr9tUpFcHHWSVKdl2ren_qxLLI-s')
    latlng = g.latlng
    location = "{},{}".format(latlng[0], latlng[1])
    key = "AIzaSyA-xvMIr9tUpFcHHWSVKdl2ren_qxLLI-s"
    #set up URL for google's api call
    URL2 = "https://maps.googleapis.com/maps/api/place/textsearch/json?location={}&query={}&key={}".format(location,keyword,key)
    #sends the http request to google's server
    r2 = requests.get(URL2)
    #checks the status code
    if r2.status_code == 200:
        first_output = r2.json()
        doc_place = first_output['results'][0]['name']
        address = first_output['results'][0]['formatted_address']
        speech_output = "I have found a possible therapist for you. It is {}. This person is located at {}".format(doc_place, address)
    else:
        print("Sorry, I'm having trouble doing that right now. Please try again later.")
    
    session_attributes = {
        'lastSpoken' : speech_output
    }
    card_title = "Therapist Function"
    reprompt_text = "I did not understand your command. " \
                    "Try saying, ASADA help, for help talking to me"
    should_end_session = False
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))
   
'''
Looking for an intent that and determining which intent to utilize
'''
def on_intent(intent_request, session, context):
    """ Called when the user specifies an intent for this skill """

    print("on_intent requestId=" + intent_request['requestId'] +
          ", sessionId=" + session['sessionId'])

    intent = intent_request['intent']
    intent_name = intent_request['intent']['name']
    
    global USER_IDENTIFICATION
    write_to_conversation(USER_IDENTIFICATION, 1, intent_name)
    
    if intent_name == "AMAZON.HelpIntent":
        return help_asada()
    elif intent_name == "DeathAlert":
        return death_alert()
    elif intent_name == "FortuneCookie":
        return fortune_cookie()
    elif intent_name == "ExerciseHabits":
        return exercise_habits()
    elif intent_name == "AMAZON.CancelIntent" or intent_name == "AMAZON.StopIntent":
        return handle_session_end_request()
    elif intent_name == "SurveyIntent":
        return do_quiz(intent_request)
    elif intent_name == "AnswerIntent":
        return answer(intent_request, intent, session, context)
    elif intent_name == "SleepHabits" or intent_name == "EatingHabits":
        return specific_habits(intent_name)
    elif intent_name == "GiveThanks":
        return give_thanks()
    elif intent_name == "UserIntroduction":
        return user_intro(intent)
    elif intent_name == "FindTherapist":
        return find_therapist(context)
    elif intent_name == "AMAZON.RepeatIntent":
        return repeat_command(session)
    elif intent_name == "CreateAnAccount":
        return createAnAccount(intent)
    elif intent_name == "SurveyTracker":
        return survey_tracker()
    else:
        return help_asada()

'''
Session is called to end the program.
'''
def on_session_ended(session_ended_request, session):
    """ Called when the user ends the session.

    Is not called when the skill returns should_end_session=true
    """
    print("on_session_ended requestId=" + session_ended_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # closes the applications
    return handle_session_end_request()


# --------------- Main handler ------------------

def lambda_handler(event, context):
    """ Route the incoming request based on type (LaunchRequest, IntentRequest,
    etc.) The JSON body of the request is provided in the event parameter.
    """
    
    print("event.session.application.applicationId=" +
          event['session']['application']['applicationId'])
    """
    Uncomment this if statement and populate with your skill's application ID to
    prevent someone else from configuring a skill that sends requests to this
    function.
    """
    # if (event['session']['application']['applicationId'] !=
    #         "amzn1.echo-sdk-ams.app.[unique-value-here]"):
    #     raise ValueError("Invalid Application ID")
    
    if event['session']['new']:
        on_session_started({'requestId': event['request']['requestId']},
                           event['session'])
    if event['request']['type'] == "LaunchRequest":
        return on_launch(event['request'], event['session'])
    elif event['request']['type'] == "IntentRequest":
        return on_intent(event['request'], event['session'], event)
    elif event['request']['type'] == "SessionEndedRequest":
        return on_session_ended(event['request'], event['session'])
