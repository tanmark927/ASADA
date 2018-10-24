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
from datetime import date

#rds settings
rds_host  = "asada.cofr9vg9xjlm.us-east-1.rds.amazonaws.com"
name = "asadadepression"
password = "Dontbesad1"
db_name = "asadaDB"

#-------variables for survey-------

OPENING_MESSAGE = "This is the Patient Health Questionnaire. " \
                   "It will measure the status of your well-being. " \
                   "You can answer by saying not at all, several days, more than half or nearly everyday. "

SKILL_TITLE = "Patient Health Questionnaire"
BEGIN_STATEMENT = "You will be asked 9 questions about problems you have faced in the past two weeks. "
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

def write_to_conversation(userID, outgoing, message):
    
    with conn.cursor() as cursor:
        now = datetime.datetime.now()
        date = now.strftime("%Y-%m-%d")
        print(message)
        sql = "INSERT INTO Conversation (UserID, outgoing, dateSent, message) VALUES ({0}, {1}, '{2}', '{3}');".format(userID, outgoing, date, message)
        cursor.execute(sql)
    conn.commit()

def build_speechlet_response(title, output, reprompt_text, should_end_session):
    return {
        'outputSpeech': {
            'type': 'PlainText',
            'text': output
        },
        'card': {
            'type': 'Simple',
            'title': "SessionSpeechlet - " + title,
            'content': "SessionSpeechlet - " + output
        },
        'reprompt': {
            'outputSpeech': {
                'type': 'PlainText',
                'text': reprompt_text
            }
        },
        'shouldEndSession': should_end_session
    }


def build_response(session_attributes, speechlet_response):
    return {
        'version': '1.0',
        'sessionAttributes': session_attributes,
        'response': speechlet_response
    }


ITEMS = []
ITEMS.append("How often are you bothered with feeling little interest or pleasure in doing things?")
ITEMS.append("How often are you bothered with feeling down, depresed or hopelessness?")
ITEMS.append("How often do you have trouble falling asleep, staying asleep, or sleeping too much?")
ITEMS.append("How often are you feeling tired or having little energy for activities?")
ITEMS.append("How often are you bothered with a poor appetite or overeating?")
ITEMS.append("How often are you having bad thoughts about yourself?")
ITEMS.append("How often have you had trouble concentrating on an activity?")
ITEMS.append("How often are you bothered with moving or speaking slowly? Or the opposite, feeling fidgety or restless")
ITEMS.append("How often have you had thoughts that you are better off dead or thought of hurting yourself in some way?")


# --------------- Functions that control the skill's behavior ------------------

def get_welcome_response():
    card_title = "Welcome"
    speech_output = "Hello. " \
                    "Welcome to ASADA. " \
                    "I will be your personal therapist. " \
                    "If you need help, try saying, " \
                    "ASADA help, for help talking to me"
    reprompt_text = "I will be your personal therapist. " \
                    "Try saying, ASADA help, for help talking to me"
    session_attributes = {
        'lastSpoken' : speech_output
    }
    should_end_session = False
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

def handle_session_end_request():
    card_title = "Session Ended"
    speech_output = "Thank you for using ASADA. " \
                    "Have a nice day! "
    
    should_end_session = True
    return build_response({}, build_speechlet_response(
        card_title, speech_output, None, should_end_session))

# --------------- Events ------------------

def on_session_started(session_started_request, session):
    """ Called when the session starts """
    print("on_session_started requestId=" + session_started_request['requestId']
          + ", sessionId=" + session['sessionId'])


def on_launch(launch_request, session):
    """ Called when the user launches the skill without specifying what they
    want
    """
    print("on_launch requestId=" + launch_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # Dispatch to your skill's launch
    return get_welcome_response()

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

def help_asada():
    global USER_IDENTIFICATION
    card_title = "help function"
    speech_output = "You can request a well being survey, ask for general advice, " \
                    "ask for more specific advice like eating, sleeping and exercise, " \
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

def give_thanks():
    global USER_IDENTIFICATION
    card_title = "Give Thanks"
    speech_output = "You are welcome. You are free to try my other services such as the advice giver for" \
             " eating and sleeping, as well as the fortune cookie."
    reprompt_text = "I did not understand your command. " \
                    "Try saying, ASADA help, for help talking to me"
    should_end_session = False
    session_attributes = {
        'lastSpoken' : speech_output
    }
    write_to_conversation(USER_IDENTIFICATION, 0, speech_output)
    return build_response(session_attributes, build_speechlet_response(
                card_title, speech_output, reprompt_text, should_end_session))    

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


def user_intro(intent):
    global USER_IDENTIFICATION
    global QUIZSCORE
    card_title = "User Introduction"
    u_name =  intent['slots']['FirstName']['value']

    with conn.cursor() as cur:
        try:
            cur.execute("select UserID from Users where UserName = %s LIMIT 1", [u_name])
            result = cur.fetchone()
            
            #NOTE: None and type(None) are NOT the same type! type(None) is NoneType,
            # which can be found in result if result contains zero elements
            if type(result) is not type(None):
                USER_IDENTIFICATION = result[0]
            
            cur.execute("select SurveyScore from Survey where UserID = %s order by SurveyDate desc limit 1", [USER_IDENTIFICATION])
            result_two = cur.fetchone()
            if type(result_two) is not type(None):
                QUIZSCORE = result_two[0]
            
            if(type(result) is not type(None) and type(result_two) is not type(None)):
                speech_output = "Welcome " + u_name + " to ASADA."
            elif(type(result) is not type(None) and type(result_two) is type(None)):
                speech_output = "Welcome " + u_name + " to ASADA. Please take a survey so that I can better target your needs."
            else:
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
        
def exercise_habits():
    #test run to get exercise advice
    global USER_IDENTIFICATION
    global QUIZSCORE
    card_title = "Exercise Habits"
    result = ""
    exercise_intensity = 0
    with conn.cursor() as cur:
        cur.execute("select * from Conversation order by conversationID desc limit 1;")
        first_result = cur.fetchone()
        well_being = calculate_well_being(globals()['QUIZSCORE'])

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

def sleep_habits():
    global USER_IDENTIFICATION
    global QUIZSCORE
    card_title = "Sleep Habits"
    result = ""
    with conn.cursor() as cur:
        well_being = calculate_well_being(globals()['QUIZSCORE'])
        severity = severity_calculator(well_being)

        cur.execute("select advice from SleepAdvice where severity = %s ORDER BY RAND() LIMIT 1", [severity])
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
    
def eating_habits():
    global USER_IDENTIFICATION
    global QUIZSCORE
    card_title = "Eating Habits"
    result = ""
    with conn.cursor() as cur:
        well_being = calculate_well_being(globals()['QUIZSCORE'])
        severity = severity_calculator(well_being)

        cur.execute("select advice from EatingAdvice where severity = %s ORDER BY RAND() LIMIT 1", [severity])
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
#-----------------------Quiz function---------------#
def ask_question(request, speech_output):
    global QUIZSCORE
    global COUNTER
    global STATE
    #reset COUNTER
    if globals()['COUNTER'] <= 0:
        globals()['COUNTER'] = 0
        speech_output += OPENING_MESSAGE
    
    globals()['COUNTER'] += 1

    quiz_question = str(ITEMS[COUNTER - 1])
    speech_output += quiz_question
    card_title = "Question" + str(COUNTER)
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

def do_quiz(request):
    global QUIZSCORE
    global COUNTER
    global STATE
    
    COUNTER = 0
    QUIZSCORE = 0
    STATE = STATE_SURVEY
    return ask_question(request, "")

def answer(request, intent, session):
    global STATE
    
    if STATE == STATE_SURVEY:
        return answer_quiz(request, intent, session)
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
    
def answer_quiz(request, intent, session):
    global QUIZSCORE
    global COUNTER
    global STATE
    global USER_IDENTIFICATION
    
    speech_message = ""
    quiz_question = ""
    
    #check if first question, and put welcome message?
    
    if session['attributes'] and session['attributes']['quizscore'] != None:
        QUIZSCORE = session['attributes']['quizscore']
    if 'Answer' in intent['slots']:
        QUIZSCORE += int(intent['slots']['Answer']['resolutions']['resolutionsPerAuthority'][0]['values'][0]['value']['id'])
        
    if COUNTER < len(ITEMS):
        return ask_question(request, "")
    speech_message += get_result(QUIZSCORE)
    
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
    
    
def get_result(score):
    if(score >= 0 and score <= 4):
        return "based on your screening, You should consult with ASADA at least once every two weeks."
    elif(score >= 5 and score <= 9):
        return "based on your screening, You should consult with ASADA at least once every few days. It is recommended to take the survey every two weeks."
    elif(score >= 10 and score <= 14):
        return "based on your screening, You should consult with ASADA at least once a day. It is recommended to take the survey every two weeks."
    elif(score >= 15 and score <= 20):
        return "based on your screening, You should consult with ASADA once a day." \
        "It is recommended to seek professional help. It is recommended to take the survey every two weeks."
    elif(score > 20):
        return "based on your screening, You should consult your doctor about your condition. There are lots of treatment options, " \
        "and getting onto it as soon as possible could bring your life back. It is recommended to take the survey every two weeks."
         
def on_intent(intent_request, session):
    """ Called when the user specifies an intent for this skill """

    print("on_intent requestId=" + intent_request['requestId'] +
          ", sessionId=" + session['sessionId'])

    intent = intent_request['intent']
    intent_name = intent_request['intent']['name']
    
        #for key in event.key():
    #    message = message + " " + key
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
        return answer(intent_request, intent, session)
    elif intent_name == "SleepHabits":
        return sleep_habits()
    elif intent_name == "EatingHabits":
        return eating_habits()
    elif intent_name == "GiveThanks":
        return give_thanks()
    elif intent_name == "UserIntroduction":
        return user_intro(intent)
    elif intent_name == "AMAZON.RepeatIntent":
        return repeat_command(session)
    else:
        raise ValueError("Invalid intent")


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
        return on_intent(event['request'], event['session'])
    elif event['request']['type'] == "SessionEndedRequest":
        return on_session_ended(event['request'], event['session'])
    
