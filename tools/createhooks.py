import requests
import json
import re
from ciscosparkapi import CiscoSparkAPI

spark_token = 'ODhkNTE1NjAtODBkZS00MzRjLWFiMjEtZWU5ZDdhNTIxODg4YWI0MDA1MDktMmJm'
spark = CiscoSparkAPI(access_token=spark_token)

headers = {
    'authorization': "Bearer " + spark_token,
    'content-type': "application/json; charset=utf-8",
    'cache-control': "no-cache",    
    }

#grab list of rooms that Jo is in
url = "https://api.ciscospark.com/v1/rooms"
response = requests.request("GET", url, headers=headers)

#Get all but the last response into the list
rooms = []
if 'Link' in response.headers:
    while 'Link' in response.headers and 'next' in response.headers['Link']:
        s = response.headers['Link']
        m = re.search(r'<.*>', s)
        link = m.group(0)[1:-1]
        res = json.loads(response.text)['items']
        for id in res:
            rooms.append(id)
        response = requests.request("GET", link, headers=headers)

#Get the last response
res = json.loads(response.text)['items']
for id in res:
    rooms.append(id)

#create the webhook for adding Jo to a room
url = "https://api.ciscospark.com/v1/webhooks"
payload = "{\n\t\t\"name\": \"Jo added to room\",\n\t\t\"targetUrl\": \"http://ec2-54-236-245-54.compute-1.amazonaws.com:8000//added\",\n\t\t\"resource\": \"memberships\",\n\t\t\"event\": \"created\",\n\t\t\"filter\": \"personEmail=jobott@sparkbot.io\"\n}"
response = requests.request("POST", url, data=payload, headers=headers)
print response.text

#create new webhooks for each room
for room in rooms:
    roomId = room['id']
    try:
        roomName = spark.rooms.get(roomId).title
        print 'Creating webhook for: ' + roomName
        spark.webhooks.create(name=roomName, targetUrl='http://ec2-54-236-245-54.compute-1.amazonaws.com:8000/webhook', resource='messages', event='created', filter="roomId=%s" % roomId)
    except Exception as e:
        if '429' in str(e):
            sleep_time = int(e.response.headers['Retry-After'])
            if sleep_time > 60:
                sleep_time = 60
            print 'Sleeping for', sleep_time, 'seconds'
            time.sleep(sleep_time)
            spark.webhooks.create(name=roomName, targetUrl='http://ec2-54-236-245-54.compute-1.amazonaws.com:8000/webhook', resource='messages', event='created', filter="roomId=%s" % roomId)
        else:
            print('Error creating webhook for %s: %s' % (roomId, e))
            pass
