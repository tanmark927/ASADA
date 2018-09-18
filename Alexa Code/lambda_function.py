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

#QUESTION_COUNT = 9

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

#-------class to contain -------
#class has frequency, attach number to name
#not at all - 0
#several days - 1
#more than half - 2
#nearly every day - 3


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


#------------------Question class---------------------------#
class Question: 
	count = 0
	
	def __init__(self, question):
        self.question = question
        Question.count += 1
	
	@staticmethod
	def get_question():
		return self.question
	
	@staticmethod
	def get_point():
		return self.point
	def set_point(self, x):
		self.point = x
	def get_text_description(self):
		text = "index: " + self.index + " out of " + Question.count + "\n"
		text += "question: " + self.question + "\n"
		text += "point: " + self.point + "\n"
		
ITEMS = []
ITEMS.append(Question("Over the past 2 weeks, how often are you bothered with feeling little interest or pleasure in doing things?"))
ITEMS.append(Question("Over the past 2 weeks, how often are you bothered with feeling down, depresed or hopelessness?"))
ITEMS.append(Question("Over the past 2 weeks, how often do you have trouble falling aslkeep, staying asleep, or sleeping too much?"))
ITEMS.append(Question("Over the past 2 weeks, how often are you feeling tired or having little energy for activities?"))
ITEMS.append(Question("Over the past 2 weeks, how often are you bothered with a poor appetite or overeating?"))
ITEMS.append(Question("Over the past 2 weeks, how often are you having bad thoughts about yourself?"))
ITEMS.append(Question("Over the past 2 weeks, how often have you had trouble concentrating on an activity?"))
ITEMS.append(Question("Over the past 2 weeks, how often are you bothered with moving or spekaing slowly? Or the opposite, feeling fidgety or restless"))
ITEMS.append(Question("Over the past 2 weeks, how often have you had thoughts that you are better off dead or thought of hurting yourself in some way?"))

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
    speech_output = "Please call 911 or the sucide hotline 1 800 273 8255"
    reprompt_text = "I did not understand your command. " \
        "You can say take a test, give me an advice or just talk."
    should_end_session = False
    write_to_conversation(2222, 0, speech_output)
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

#TODO: implement count, grab from the database. return a random choice from the size
def fortune_cookie():
    #test run to grab a fortune cookie
    session_attributes = {}
    card_title = "Fortune Cookie"
    result = ""
    with conn.cursor() as cur:
        cur.execute("select FC_Message from FortuneCookie ORDER BY RAND() LIMIT 1")
        result = cur.fetchone()
        speech_output = result[0]
        reprompt_text = "I did not understand your command. " \
        "You can say take a test, give me an advice or just talk."
        should_end_session = False
        write_to_conversation(2222, 0, speech_output)
        return build_response(session_attributes, build_speechlet_response(
                card_title, speech_output, reprompt_text, should_end_session))
    

def ask_question(request, speech_output):
    #reset COUNTER
    if globals()['COUNTER'] <= 0:
        globals()['COUNTER'] = 0
        speech_output = OPENING_MESSAGE
    
    globals()['COUNTER'] += 1
    
    item_cls = ITEMS[COUNTER - 1]
    quiz_question = item_cls.get_question() #TODO: Create method
    speech_output += quiz_question
    card_title = "Question" + str(COUNTER)
    session_attributes = {"quizscore":globals()['QUIZSCORE'],
                  "quizproperty":quiz_question,
                  "response":speech_output,
                  "state": globals()['STATE'],
                  "counter":globals()['COUNTER'],
                  "quizitem":item_cls.__dict__
                 }
    should_end_session = True
        return build_response(session_attributes, build_speechlet_response(
                card_title, speech_output, reprompt_text, should_end_session))    

def do_quiz(request):
    session_attributes = {}
	global surveyscore
	global COUNTER
	global state
    state = STATE_SURVEY
    card_title = "Begin Survey"
    speech_output = OPENING_MESSAGE
    reprompt_text = "I did not understand your command. "
    should_end_session = True
	return ask_question(request, "")
   # return build_response(session_attributes, build_speechlet_response(
    #    card_title, speech_output, reprompt_text, should_end_session))

def answer(request, intent, session):
    global STATE
    
    if STATE == STATE_SURVEY:
        return answer_quiz(request, intent, session)
    speech_output = "You are not in the Depression screening process at the moment. You can say take the survey or start the survey"
    card_title = "Gave survey answers while not in survey process"
    should_end_session = True
    reprompt_text = "I did not understand your command. "
    return build_response(session_attributes, build_speechlet_response(
                card_title, speech_output, reprompt_text, should_end_session))
    
def answer_quiz(request, intent, session):
    global QUIZSCORE
    global COUNTER
    global STATE
    
    speech_output = ""
    quiz_question = ""
    
    

#TODO FOR ASADA: change intents to be appropriate with our functions
def on_intent(intent_request, session):
    """ Called when the user specifies an intent for this skill """

    print("on_intent requestId=" + intent_request['requestId'] +
          ", sessionId=" + session['sessionId'])

    intent = intent_request['intent']
    intent_name = intent_request['intent']['name']
    get_state(session)
    
    
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
    elif intent_name == "AMAZON.CancelIntent" or intent_name == "AMAZON.StopIntent":
        return handle_session_end_request()
    elif intent_name == "SurveyIntent":
        return do_quiz(request)
    elif intent_name == "AnswerIntent":
        return answer(request, intent, session)
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
    
