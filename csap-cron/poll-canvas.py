from ciscosparkapi import CiscoSparkAPI
import time
from pytz import timezone
import pytz
import dateutil.parser
from datetime import datetime
import json
import pandas as pd
from tzlocal import get_localzone
import sys
sys.path.append("/home/ec2-user/csap/canvas")
from read import CanvasReader

def threshold(days=0, hours=0, minutes=0, seconds=0):
    return days*24*3600 + hours*3600 + minutes*60 + seconds

DEFAULT_THRESHOLD = threshold(days=7)
canvas_token = '9881~NaOD1DvHAF1mFhmyORwMkNzmUb7saHTHUQKmvexWdnEFoRmTQ3QuvVuqvuGnacKk'
base_url = 'https://ciscoacademy.test.instructure.com'
api_prefix = '/api/v1'
canvas = CanvasReader(canvas_token, base_url, api_prefix, verbose=False)
spark_token = 'OGM5YTM4NjYtYWIzZC00YzcwLThhZmMtZmEwOTZlZGRhNTU0YzNhMDQ4YjAtNWEx'
spark = CiscoSparkAPI(access_token=spark_token)

def user_in_team(user_id, team_id):
    member_ids = [membership.personEmail for membership in spark.team_memberships.list(teamId=team_id)]
    return user_id in member_ids

def add_user_to_team(user_id, team_id):
    spark.team_memberships.create(teamId=team_id, personEmail=user_id)
    
def add_user_to_room(user_id, room_id):
    spark.memberships.create(roomId=room_id,
                               personEmail=user_id)

def create_group_with_users(ids, title, startingMessage, teamId=None):
    room = spark.rooms.create(title, teamId)
    spark.webhooks.create(name=room.id,
                          targetUrl='http://ec2-13-58-221-119.us-east-2.compute.amazonaws.com:8000/webhook',
                          resource='messages',
                          event='created',
                          filter="roomId=%s" % room.id)
    for id in ids:
        if teamId:
            if not user_in_team(id, teamId): # If user not in team, add to team
                add_user_to_team(id, teamId)
        add_user_to_room(id, room.id) # Add user to room
    spark.messages.create(roomId=room.id, markdown=startingMessage)
    
def get_team_id(teamname):
    teamdf = pd.read_csv('../csap-data/teams.csv')
    return teamdf[teamdf.team==teamname].id.item()
    
def create_room_for_section(section):
    create_group_with_users(ids=[student['login_id'] for student in section['students']],
                            title=section['course_name'],
                            startingMessage="Hey there! I'm CSAP Bot, and I'll be your CSAP resource through the %s module. Try saying /help to see all the awesome things I can do!" % section['course_name'],
                            teamId=get_team_id(section['name']))

subaccount_name = 'FY18Q1 Cisco Sales Associates Program (CSAP)'
def find_sections():
    res = []
    log = '*Polling Canvas for upcoming sections . . .*<br><br>'
    for course in canvas.get_courses_for_subaccount(subaccount_name):
        course_id = course['id']
        sections = canvas.get_sections(course_id)
        for section in sections:
            start = section['start_at']
            if start:
                tz = timezone(course['time_zone'])
                dt = dateutil.parser.parse(start, tzinfos=[tz])
                ts = (dt - datetime(1970, 1, 1, tzinfo=pytz.utc)).total_seconds()
                now = time.time()
                diff = ts-now
                if diff > 0 and diff < DEFAULT_THRESHOLD:
                    section['course_name'] = course['name']
                    section['course_tz'] = course['time_zone']
                    res.append(section)
                    log += str(tz) + '<br>'
                    log += str(start) + '<br>'
                    log += '**The %s section for %s starts in %f hours.**<br><br>' % (section['name'], section['course_name'], diff/3600)
    if len(res) == 0:
        log += 'There are no sections starting soon.'
    return (res, log)

sections, log = find_sections()
created = pd.read_csv('../csap-data/created.csv')
for section in sections:
    if section['id'] in list(created.id):
        row = created[created.id==section['id']]
        diff = time.time() - row['timestamp'].item()
        log += "The room for %s (%s) was created %f hours ago.<br>" % (row['course'].item(), row['section'].item(), diff/3600)
    else:
        log += "**Creating the room for %s (%s) . . .**<br>" % (section['course_name'], section['name'])
        create_room_for_section(section)
        newdf = pd.DataFrame({"id": [section['id']],
                              "course": [section['course_name']],
                              "section": [section['name']],
                              "timestamp": [time.time()]})
        with open('../csap-data/created.csv', 'a') as f:
            newdf.to_csv(f, header=False, columns=['id', 'course', 'section', 'timestamp'])


print('%s: %s' % (datetime.now().time(), log))

spark.messages.create(roomId='Y2lzY29zcGFyazovL3VzL1JPT00vZDQ0YzkyYjAtNGJhMy0xMWU3LTkyYzYtOGIyNWUzNDAxNzM4',
                     markdown=log)
