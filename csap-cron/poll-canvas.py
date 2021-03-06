from ciscosparkapi import CiscoSparkAPI
import time
import urllib3
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

DEFAULT_THRESHOLD = threshold(hours=-138)
old_canvas_token = '9881~ZKTdBPBwOhgochgNfJad5YJp1e03Mc0DVyt2B6OSkkSomA7hhXfFZBU8yG9lpB2k'
canvas_token = '9881~2QiAZJEE1abpIwZ58N5Gufn4cl2qXuRdWZFfOzPX4HII5NHxuFQKHZg1X3sDgrO0'
base_url = 'https://ciscoacademy.instructure.com'
api_prefix = '/api/v1'
canvas = CanvasReader(canvas_token, base_url, api_prefix, verbose=False)
spark_token = 'ODhkNTE1NjAtODBkZS00MzRjLWFiMjEtZWU5ZDdhNTIxODg4YWI0MDA1MDktMmJm'
spark = CiscoSparkAPI(access_token=spark_token)

roles = ['ASR', 'ASE', 'ASX']
locations = ['RTP', 'SJC', 'EMEAR II', 'EMEAR I', 'EMEAR', 'AMS II', 'AMS I', 'AMS', 'SNG', 'APJC', 'Americas']
asx_locations = ['Team 1', 'Team 2', 'Team 3', 'Team 4', 'Team 5', 'Team 6', 'Team 7', 'Team 8', 'Team 9', 'Team 10', 'Team 11']


def user_in_team(user_id, team_id):
    member_ids = [membership.personEmail for membership in spark.team_memberships.list(teamId=team_id)]
    return user_id in member_ids

def add_user_to_team(user_id, team_id):
    print("Adding user %s to team %s." % (user_id, team_id))
    try:
        spark.team_memberships.create(teamId=team_id, personEmail=user_id)
    except Exception as e:  
        if '429' in str(e):    
            sleep_time = int(e.response.headers['Retry-After'])
            if sleep_time > 60:
                sleep_time = 60
            print 'Sleeping for', sleep_time, 'seconds' 
            time.sleep(sleep_time)
            add_user_to_team(user_id, team_id)
        else:
            print('Error adding user %s to team %s: %s' % (user_id, team_id, e))
            pass
                

def add_user_to_room(user_id, room_id):
    try:
        print("Adding user %s to room %s." % (user_id, room_id))
        spark.memberships.create(roomId=room_id,
                                   personEmail=user_id)
    except Exception as e:
        if '429' in str(e):
            sleep_time = int(e.response.headers['Retry-After'])
            if sleep_time > 60:
                sleep_time = 60
            print 'Sleeping for', sleep_time, 'seconds'                       
            time.sleep(sleep_time)
            add_user_to_room(user_id, room_id)
        else:
            print('Error adding user %s to room %s: %s' % (user_id, room_id, e))
            pass

def create_room_wrapper(title, teamId):
    try:
        room = spark.rooms.create(title, teamId)
        return room
    except Exception as e:
        if '429' in str(e):
            sleep_time = int(e.response.headers['Retry-After'])
            if sleep_time > 60:
                sleep_time = 60
            print 'Sleeping for', sleep_time, 'seconds'
            time.sleep(sleep_time)
            create_room_wrapper(title, teamId)
        else:
            print('Error creating room: %s' % (title))
            pass

def create_webhook_wrapper(title, teamId, room):
    try:
        print("Creating webhook for %s." % (room.id))
        spark.webhooks.create(name=room.id,
                              targetUrl='http://ec2-34-201-162-247.compute-1.amazonaws.com:8000/webhook',
                              resource='messages',
                              event='created',
                              filter="roomId=%s" % room.id)
    except Exception as e:
        if '429' in str(e):
            sleep_time = int(e.response.headers['Retry-After'])
            if sleep_time > 60:
                sleep_time = 60
            print 'Sleeping for', sleep_time, 'seconds'
            time.sleep(sleep_time)
            create_webhook_wrapper(title, teamId)
        else:
            print('Error creating webhook for %s: %s' % (title, e))
            pass

def create_group_with_users(ids, title, startingMessage, teamId=None):

    room = create_room_wrapper(title, teamId)
    
    #removing this so there is not duplicate
    #create_webhook_wrapper(title, teamId, room)
    
    for id in ids:
        if teamId:
            if not user_in_team(id, teamId): # If user not in team, add to team
                add_user_to_team(id, teamId)
        add_user_to_room(id, room.id) # Add user to room
    spark.messages.create(roomId=room.id, markdown=startingMessage)
    return room.id

def get_team_id(teamname):
    teamdf = pd.read_csv('/home/ec2-user/csap/csap-data/teams.csv')
    print teamdf[teamdf.team==teamname].id
    print teamname
    return teamdf[teamdf.team==teamname].id.item()

def create_room_for_section(section):
    ids = [student['login_id'] for student in section['students']]
    if section['instructor']:
        ids.append(section['instructor'])
    else:
        print('No instructor found for %s.' % section['course_name'])
    room_id = create_group_with_users(ids=ids,
                            title=section['course_name'],
                            startingMessage="Hey there! I'm Jo, and I'll be your resource through the %s module, facilitated by %s. Try saying /help to see all the awesome things I can do, and remember to tag me with `@Jo` first! Click  <a href='%s/courses/%s'>here</a> to access your course dashboard. This is my first time being used in CSAP, so please let Leigh Pember (lpember) know if I'm not working or if I do anything unexpected!" % (section['course_name'], section['instructor'], base_url, section['course_id']),
                            teamId=get_team_id(section['role'] + ' ' +section['location']))
    return room_id

subaccount_name = 'FY18Q1 Cisco Sales Associates Program (CSAP)'
def find_sections():
    instructors = pd.read_csv('/home/ec2-user/csap/csap-data/instructors.csv')
    res = []
    log = '*Polling Canvas for upcoming sections . . .*<br><br>'
    log += 'The following sections are formatted differently on Canvas. Logs are printed in the format `section_name`, `course_name`, `role`, `location`, `instructor`.<br><br>'
    for course in canvas.get_courses_for_subaccount(subaccount_name):
        course_id = course['id']
        sections = canvas.get_sections(course_id)
        for section in sections:
            start = section['start_at']
            if start:

                location = None
                role = None
                instructor = None

                # Find role
                for r in roles:
                    if r in course['name']:
                        role = r

                # Find location
                if role == 'ASX':
                    for l in asx_locations:
                        if l in section['name']:
                            location = l
                else:
                    for l in locations:
                        print('checking %s against %s') % (l, section['name'])
                        if l in section['name']:
                            print('Success! Found %s in %s') % (l, section['name'])
                            location = l
                            break

                # Find instructor
                if '-' in section['name']:
                    instructor = section['name'].split('-')[-1].strip()
                    name = instructor.split(' ')
                    query = instructors[(instructors.first_name == name[0]) & (instructors.last_name == name[1])].email
                    if len(query) == 1:
                        instructor = query.item()

                if not role or not location or not instructor:
                    log += '%s, %s, ' % (section['name'], course['name'])
                    if role:
                        log += '%s, ' % role
                    else:
                        log += '**%s, **' % role
                    if location:
                        log += '%s, ' % location
                    else:
                        log += '**%s, **' % location
                    if instructor:
                        log += '%s' % instructor
                    else:
                        log += '**%s**<br>' % instructor

                if role and location:
                    tz = timezone(course['time_zone'])
                    dt = dateutil.parser.parse(start, tzinfos=[tz])
                    ts = (dt - datetime(1970, 1, 1, tzinfo=pytz.utc)).total_seconds()
                    now = time.time()
                    diff = ts-now
                    if diff < DEFAULT_THRESHOLD:
                        print('got to %s and %s %s. diff is: %s') % (role, location, course['name'], diff)
                        print course['name']
                        section['course_name'] = course['name']
                        section['course_tz'] = course['time_zone']
                        section['start_unix'] = ts
                        section['role'] = role
                        section['location'] = location
                        section['instructor'] = instructor
                        res.append(section)
    return (res, log)

sections, log = find_sections()
if len(sections) == 0:
    log += '<br>There are no sections starting soon.'
else:
    for section in sections:
        print(section)
        log += '<br>**The %s section for %s starts in %f hours.**<br>' % (section['name'], section['course_name'], (section['start_unix']-time.time())/3600)
print(log)

created = pd.read_csv('/home/ec2-user/csap/csap-data/created.csv')
for section in sections:
    if section['id'] in list(created.id):
        #row = created[created.id==section['id']]
        #diff = time.time() - row['timestamp'].item()
        #log += "The room for %s (%s) was created %f hours ago.<br>" % (row['course'].item(), row['section'].item(), diff/3600)
        pass
    else:
        log += "**Creating the room for %s (%s) . . .**<br>" % (section['course_name'], section['name'])
        room_id = create_room_for_section(section)
        created_df = pd.DataFrame({"id": [section['id']],
                              "course": [section['course_name']],
                              "section": [section['name']],
                              "timestamp": [time.time()]})
        with open('/home/ec2-user/csap/csap-data/created.csv', 'a') as f:
            created_df.to_csv(f, header=False, columns=['id', 'course', 'section', 'timestamp'])
        question_df = pd.DataFrame(columns=['user_id', 'first_name', 'last_name', 'email', 'question', 'timestamp'])
        question_df.to_csv('/home/ec2-user/csap/csap-data/questions/%s.csv' % (room_id))

print('%s: %s' % (datetime.now().time(), log))

spark.messages.create(roomId='Y2lzY29zcGFyazovL3VzL1JPT00vZDQ0YzkyYjAtNGJhMy0xMWU3LTkyYzYtOGIyNWUzNDAxNzM4',
                     markdown=log)
