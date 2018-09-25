from __future__ import print_function
import sys
import logging
import pymysql
import datetime
import math
import string
import random

#rds settings
rds_host  = "asada.cofr9vg9xjlm.us-east-1.rds.amazonaws.com"
name = "asadadepression"
password = "Dontbesad1"
db_name = "asadaDB"

#-------variables for survey-------

OPENING_MESSAGE = "This is the Patient Health Questionnaire. " \
                   "It will measure the severity and presence of depression. " \
                   "The higher your score, the more severe your depression is. "

SKILL_TITLE = "Patient Health Questionnaire"
BEGIN_STATEMENT = "You will be asked 9 questions about problems you have faced in the past two weeks. "
END_STATEMENT = "Thank you for completing the Patient Health Questionnaire. "

USE_CARDS_FLAG = False

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
ITEMS.append("Over the past 2 weeks, how often are you bothered with feeling little interest or pleasure in doing things?")
ITEMS.append("Over the past 2 weeks, how often are you bothered with feeling down, depresed or hopelessness?")
ITEMS.append("Over the past 2 weeks, how often do you have trouble falling aslkeep, staying asleep, or sleeping too much?")
ITEMS.append("Over the past 2 weeks, how often are you feeling tired or having little energy for activities?")
ITEMS.append("Over the past 2 weeks, how often are you bothered with a poor appetite or overeating?")
ITEMS.append("Over the past 2 weeks, how often are you having bad thoughts about yourself?")
ITEMS.append("Over the past 2 weeks, how often have you had trouble concentrating on an activity?")
ITEMS.append("Over the past 2 weeks, how often are you bothered with moving or spekaing slowly? Or the opposite, feeling fidgety or restless")
ITEMS.append("Over the past 2 weeks, how often have you had thoughts that you are better off dead or thought of hurting yourself in some way?")


# --------------- Functions that control the skill's behavior ------------------

#TODO FOR ASADA: change intents to be appropriate with our functions
def get_welcome_response():
    """ If we wanted to initialize the session to have some attributes we could
    add those here
    """

    session_attributes = {}
    card_title = "Welcome"
    speech_output = "Hello. " \
                    "Welcome to ASADA. " \
                    "It will be your personal therapist. " \
                    "Ask it anything that is on your mind. "
    # If the user either does not reply to the welcome message or says something
    # that is not understood, they will be prompted again with this text.
    reprompt_text = "ASADA will be your personal therapist. " \
                    "Ask it anything that is on your mind. "
    should_end_session = False
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

def handle_session_end_request():
    card_title = "Session Ended"
    speech_output = "Thank you for using ASADA. " \
                    "Have a nice day! "
    # Setting this to true ends the session and exits the skill.
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
    if score >= 0 && score <= 4:
        return 5;
    elif score >= 5 && score <= 9:
        return 4;
    elif score >= 10 && score <= 14:
        return 3;
    elif score >= 15 && score <= 20:
        return 2;
    elif score > 20:
        return 1;

def help_asada():
    #help function for asada
    session_attributes = {}
    card_title = "help function"
    speech_output = "You can say, take a test, give me an advice, or just talk"
    reprompt_text = "I did not understand your command. " \
        "You can say take a test, give me an advice or just talk."
    should_end_session = False
    write_to_conversation(2222, 0, speech_output)
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))
    
def death_alert():
    #emergency suicide alert
    session_attributes = {}
    card_title = "911 emergency function"
    speech_output = "ASADA recommends you call 911 or the suicide hotline 1 800 273 8255"
    reprompt_text = "I did not understand your command. " \
        "You can say take a test, give me an advice or just talk."
    should_end_session = False
    write_to_conversation(2222, 0, speech_output)
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

def fortune_cookie():
    #test run to grab a fortune cookie
    session_attributes = {}
    card_title = "Fortune Cookie"
    result = ""
    with conn.cursor() as cur:
        #change query later to tie more closely to survey
        cur.execute("select FC_Message from FortuneCookie ORDER BY RAND() LIMIT 1")
        result = cur.fetchone()
        speech_output = result[0]
        reprompt_text = "I did not understand your command. " \
        "You can ask ASADA to give a survey, give advice or just talk."
        should_end_session = False
        write_to_conversation(2222, 0, speech_output)
        return build_response(session_attributes, build_speechlet_response(
                card_title, speech_output, reprompt_text, should_end_session))

def exercise_habits():
    #test run to get exercise advice
    session_attributes = {}
    card_title = "Exercise Habits"
    result = ""
    exercise_intensity = 0
    with conn.cursor() as cur:
        cur.execute("select * from Conversation order by conversationID desc limit 1;")
        first_result = cur.fetchone()
        well_being = calculate_well_being(QUIZSCORE)

        if 'arms' in first_result:
            # cur.execute("select FA_Description from FitnessActivity where FA_Category = 'arms' and FA_Intensity = %s ORDER BY RAND() LIMIT 1", [well_being])
            cur.execute("select FA_Description from FitnessActivity where FA_Category = 'arms' ORDER BY RAND() LIMIT 1")
            result = cur.fetchone()
        elif 'legs' in first_result:
            # cur.execute("select FA_Description from FitnessActivity where FA_Category = 'legs' and FA_Intensity = %s ORDER BY RAND() LIMIT 1", [well_being])
            cur.execute("select FA_Description from FitnessActivity where FA_Category = 'legs' ORDER BY RAND() LIMIT 1")
            result = cur.fetchone()
        elif 'chest' in first_result:
            # cur.execute("select FA_Description from FitnessActivity where FA_Category = 'chest' and FA_Intensity = %s ORDER BY RAND() LIMIT 1", [well_being])
            cur.execute("select FA_Description from FitnessActivity where FA_Category = 'chest' ORDER BY RAND() LIMIT 1")
            result = cur.fetchone()
        elif 'back' in first_result:
            # cur.execute("select FA_Description from FitnessActivity where FA_Category = 'back' and FA_Intensity = %s ORDER BY RAND() LIMIT 1", [well_being])
            cur.execute("select FA_Description from FitnessActivity where FA_Category = 'back' ORDER BY RAND() LIMIT 1")
            result = cur.fetchone()
        else:
            #execute this query if user command does not specify area of exercise
            cur.execute("select FA_Description from FitnessActivity ORDER BY RAND() LIMIT 1")
            result = cur.fetchone()
            
        speech_output = result[0]
        reprompt_text = "I did not understand your command. " \
        "You can ask ASADA to give a survey, give advice or just talk."
        should_end_session = False
        write_to_conversation(2222, 0, speech_output)
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
    #retrieve a piece of sleep advice for the user
    session_attributes = {}
    card_title = "Sleep Habits"
    result = ""
    with conn.cursor() as cur:
        well_being = calculate_well_being(QUIZSCORE)
        severity = severity_calculator(well_being)

        #cur.execute("select advice from SleepAdvice where severity = %s ORDER BY RAND() LIMIT 1", [severity])
        #comment or erase below query if above query is present
        cur.execute("select advice from SleepAdvice ORDER BY RAND() LIMIT 1")
        result = cur.fetchone()
        speech_output = result[0]
        reprompt_text = "I did not understand your command. " \
        "You can ask ASADA to give a survey, give advice or just talk."
        should_end_session = False
        write_to_conversation(2222, 0, speech_output)
        return build_response(session_attributes, build_speechlet_response(
            card_title, speech_output, reprompt_text, should_end_session))
    
def eating_habits():
    #retrieve a piece of eating advice for the user
    session_attributes = {}
    card_title = "Eating Habits"
    result = ""
    with conn.cursor() as cur:
        well_being = calculate_well_being(QUIZSCORE)
        severity = severity_calculator(well_being)
        
        #cur.execute("select advice from EatingAdvice where severity = %s ORDER BY RAND() LIMIT 1", [severity])
        #comment or erase below query if above query is present        
        cur.execute("select advice from EatingAdvice ORDER BY RAND() LIMIT 1")
        result = cur.fetchone()
        speech_output = result[0]
        reprompt_text = "I did not understand your command. " \
        "You can ask ASADA to give a survey, give advice or just talk."
        should_end_session = False
        write_to_conversation(2222, 0, speech_output)
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

    quiz_question = str(ITEMS[COUNTER - 1]) #TODO: Create method
    speech_output += quiz_question
    card_title = "Question" + str(COUNTER)
    session_attributes = {"quizscore":globals()['QUIZSCORE'],
                  "quizproperty":quiz_question,
                  "response":speech_output,
                  "state": globals()['STATE'],
                  "counter":globals()['COUNTER'],
                 }
  
    reprompt_text = "I did not understand your command. " \
        "You can ask ASADA to give a survey, give advice or just talk."
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
    return build_response(session_attributes, build_speechlet_response(
                card_title, speech_output, reprompt_text, should_end_session))
    
def answer_quiz(request, intent, session):
    global QUIZSCORE
    global COUNTER
    global STATE
    
    speech_message = ""
    quiz_question = ""
    
    #check if first question, and put welcome message?
    
    if session['attributes'] and session['attributes']['quizscore'] != None:
        QUIZSCORE = session['attributes']['quizscore']
    if 'Answer' in intent['slots']:
        QUIZSCORE += int(intent['slots']['Answer']['resolutions']['resolutionsPerAuthority'][0]['values'][0]['value']['id'])
        
    if COUNTER < len(ITEMS):
        return ask_question(request, "")
    speech_message += get_finalscore(QUIZSCORE)
    speech_message += get_result(QUIZSCORE)
    
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
    
def get_finalscore(score):
    return "your final score is "+str(score)+". "
    
def get_result(score):
    if(score >= 0 and score <= 4):
        return "based on your screening, the score of " +str(score)+ " suggests minimal or no depression, which may not need treatment. It is recommended to take the survey every two weeks as a follow-up."
    elif(score >= 5 and score <= 9):
        return "based on your screening, the score of " +str(score)+ " suggests mild depression, which may require watchful waiting and repeated survey follow-ups. It is recommended to take the survey every two weeks."
    elif(score >= 10 and score <= 14):
        return "based on your screening, the score of " +str(score)+ " suggests moderate depression severity. You may consider to see a therapist to prepare a treatment plan ranging from counseling, follow-up and possibly pharmacotherapy."
    elif(score >= 15 and score <= 20):
        return "based on your screening, the score of " +str(score)+ " suggests moderately severe depression. You should see a therapist immediately to start pharmacotherapy and possibly psychotherapy. "
    elif(score > 20):
        return "based on your screening, the score of " +str(score)+ " suggests severe depression. You should seek immediate help. Refer to a mental health specialist so you may begin treatment."
    
#TODO FOR ASADA: change intents to be appropriate with our functions
def on_intent(intent_request, session):
    """ Called when the user specifies an intent for this skill """

    print("on_intent requestId=" + intent_request['requestId'] +
          ", sessionId=" + session['sessionId'])

    intent = intent_request['intent']
    intent_name = intent_request['intent']['name']
    
    # Dispatch to your skill's intent handlers
    #if intent_name == "AdviceGiver":
    #    return AdviceGiverAction(intent, session)
    #elif intent_name == "ContinueConvo":
    #    return ContinueConvoAction(intent, session)
    #elif intent_name == "RecommendMeMusic":
    #    return MusicAction(intent, session);    
    
    
        #for key in event.key():
    #    message = message + " " + key
        
    write_to_conversation(2222, 1, intent_name)
    
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
    #elif intent_name == "AMAZON.PauseIntent" or intent_name == "AMAZON.ResumeIntent"
    #    return do_something(); 
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
    
