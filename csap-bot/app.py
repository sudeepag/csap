from flask import Flask, request
from ciscosparkapi import CiscoSparkAPI
from itertools import zip_longest
import pandas as pd
import smartsheet
import urllib
from urllib.request import urlopen
import json
import time
import random
import sys
sys.path.append("/home/ec2-user/csap/csap-data")
sys.path.append("/home/ec2-user/csap/canvas")
from config import *

# Flask Setup
app = Flask(__name__)

# Spark Setup
BOT_TOKEN = 'OGM5YTM4NjYtYWIzZC00YzcwLThhZmMtZmEwOTZlZGRhNTU0YzNhMDQ4YjAtNWEx'
api = CiscoSparkAPI(access_token=BOT_TOKEN)
#BOT_ID = api.people.me().id

# Smartsheet Setup
SS_TOKEN = '6neubu7it69y4gsl4qzhxg6zth'
SS_QUESTIONS_ID = '1170584110425988'
SS_ROSTER_ID = '168654139615108'
ss = smartsheet.Smartsheet(SS_TOKEN)
ss.errors_as_exceptions(True)

def random_question_response():
    response_bank = ["That's a great question!",
                     "Thanks for the question.",
                     "You'll have that answered soon.",
                     "Got it, someone will get back to you on that!"]
    return random.choice(response_bank)

def sendSparkGET(url):
    req = urllib.request.Request(url,
                            headers={"Accept" : "application/json",
                                     "Content-Type":"application/json"})
    req.add_header("Authorization", "Bearer "+BOT_TOKEN)
    contents = urlopen(req).read().decode('utf-8')
    return str(contents)

def format_message(message):
    print(message)
    bot_name = api.people.me().displayName
    return message[len(bot_name)+1:] if message.startswith(bot_name) else message

def send_message(roomId, message):
    api.messages.create(roomId=roomId, markdown=message)

def response_for_message(senderId, roomId, message):
    msg = message.lower()
    response = ''
    if msg == 'hey':
        response = 'Hey there! Try saying `/help` to see all the awesome things I can do!'
    elif msg == '/help':
        response = "Hey there! These are the things I can do right now.<br><br>`/question` to ask a question<br>`/list` to list all the questions<br>`/group` to randomly split a team into groups<br>`/pick` to randomly pick someone from a team<br>`/roster` to see the roster for this class"
    elif msg.startswith('/question'):
        question_text = message[len('/question')+1:]
        if len(question_text) == 0:
            response = 'Please enter a valid question in the format */question Why is CSAP Bot so awesome?*'
        else:
            store_question(roomId, senderId, message[len('/question')+1:])
            response = random_question_response()
    elif msg == '/list':
        df = pd.read_csv('/home/ec2-user/csap/csap-data/questions/%s.csv' % roomId)
        if len(df) == 0:
            response = 'There are currently no questions. To ask a question, type `/question`, followed by your question.'
        else:   
            response = 'Here are the questions currently in the question bank.<br><br>'     
            for row in df.iterrows():
                response += '**%s %s**: %s<br>' % (row[1]['first_name'], row[1]['last_name'], row[1]['question'])
                print(row)
    elif msg.startswith('/group'):
        teamId = api.rooms.get(roomId).teamId
        roomName = api.rooms.get(roomId).title
        ngroups = message[len('/group')+1:].split(' ')[0]
        if teamId and ngroups:
            people = people_in_room(roomId)
            random.shuffle(people)
            team = api.teams.get(teamId).name
            groups = grouping(people, ngroups)
            response = "I've randomly split up the %s room into groups of %d:<br>" % (roomName, int(ngroups))
            for i, group in enumerate(groups):
                print(group)
                response += '**<br>Group %d**: ' % (int(i)+1)
                try:
                    response += ', '.join(group)
                except TypeError:
                    response += group[0]
        else:
            response = "Something looks wrong! Try `/group` `Group Size` in a module room within your team, like this */group 3*"
    elif msg == '/pick':
        teamId = api.rooms.get(roomId).teamId
        if teamId:
            people = people_in_room(roomId)
            random.shuffle(people)
            response = "**%s** has been picked!" % (people[0])
        else:
            response = "Something looks wrong! Try `/pick` in a module room within your team."
    elif msg == '/roster':
        teamId = api.rooms.get(roomId).teamId
        if teamId:
            people = people_in_room(roomId)
            response += "Here's the roster for this class:<br><br>"
            for i, person in enumerate(people):
                response += '%d) %s<br>' % (i+1, person)
        else:
            response = "Something looks wrong! Try `/roster` in a module room within your team."
    return response
    
def incoming_message(req):
    # We only care about messages not sent by the bot
    senderId = req['data']['personId']
    if senderId != BOT_ID:
        res = json.loads(sendSparkGET('https://api.ciscospark.com/v1/messages/{0}'.format(req['data']['id'])))
        print(res)
        roomId = res['roomId']
        message = format_message(res['text'])
        print('INCOMING MESSAGE: '+message)
        send_message(roomId, response_for_message(senderId, roomId, message))
        
        
# HELPER METHODS

def people_in_room(roomid):
    return [membership.personDisplayName for membership in api.memberships.list(roomId=roomid) if membership.personId != BOT_ID and membership.personId != SECURITY_ID]
    
def grouping(people, n):
    args = [iter(people)] * int(n)
    return zip_longest(*args, fillvalue=None)

def store_question(room_id, user_id, question):
    user_info = api.people.get(user_id)
    newdf = pd.DataFrame({"user_id": [user_id],
                          "first_name": [user_info.firstName],
                          "last_name": [user_info.lastName],
                          "email": [user_info.emails[0]],
                          "question": [question],
                          "timestamp": [time.time()]})
    with open('/home/ec2-user/csap/csap-data/questions/%s.csv' % room_id, 'a') as f:
        newdf.to_csv(f, header=False, columns=['user_id', 'first_name', 'last_name', 'email', 'question', 'timestamp'])

# SMARTSHEET

def add_cell(column, value, mapping):
    newCell = ss.models.Cell()
    newCell.column_id = mapping[column]
    newCell.value = value
    return newCell

def add_row(columns, values, mapping):
    newRow = ss.models.Row()
    newRow.to_bottom = True
    for c, v in zip(columns, values):
        newRow.cells.append(add_cell(c, v, mapping))
    return newRow

def store_question_in_smartsheet(user_id, question):
    sheet = ss.Sheets.get_sheet(SS_QUESTIONS_ID)
    column_map = {}
    for column in sheet.columns:
        column_map[column.title] = column.id
    qid = len(sheet.rows)
    timestamp = time.time()
    user_data = api.people.get(user_id)
    row = add_row(columns=['qid', 'user_id', 'firstName', 'lastName', 'email', 'timestamp', 'question'],
                  values=[qid, user_id, user_data.firstName, user_data.lastName, user_data.emails[0], timestamp, question],
                  mapping=column_map)
    ss.Sheets.add_rows(SS_QUESTIONS_ID, [row])

class Person(object):
    def __init__(self, id, firstName, lastName, team):
        self.id = id
        self.firstName = firstName
        self.lastName = lastName
        self.team = team
        
def get_cell_by_column_name(mapping, row, column_name):
    return row.get_column(mapping[column_name])
        
def people_in_team(teamName):
    sheet = ss.Sheets.get_sheet(SS_ROSTER_ID)
    mapping = {}
    for column in sheet.columns:
        mapping[column.title] = column.id
    people = []
    for row in sheet.rows:
        id = get_cell_by_column_name(mapping, row, 'id').value
        firstName = get_cell_by_column_name(mapping, row, 'firstName').value
        lastName = get_cell_by_column_name(mapping, row, 'lastName').value
        team = get_cell_by_column_name(mapping, row, 'team').value
        if team == teamName:
            people.append(Person(id, firstName, lastName, team))
    random.shuffle(people)
    return people

#def grouping(team, n):
#   people = people_in_team(team)
#    args = [iter(people)] * int(n)
#    return zip_longest(*args, fillvalue=None)

@app.route('/')
def index():
    return 'Hello World!'

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.method == 'POST':
        incoming_message(request.json)
        return '', 200
    else:
        abort(400)

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
