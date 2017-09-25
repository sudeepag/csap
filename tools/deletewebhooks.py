import requests
import json
import re
from ciscosparkapi import CiscoSparkAPI

spark_token = 'ODhkNTE1NjAtODBkZS00MzRjLWFiMjEtZWU5ZDdhNTIxODg4YWI0MDA1MDktMmJm'
spark = CiscoSparkAPI(access_token=spark_token)

#Get a list of all webhooks that Jo has
url = "https://api.ciscospark.com/v1/webhooks"

headers = {
    'authorization': "Bearer " + spark_token,
    'content-type': "application/json; charset=utf-8",
    'cache-control': "no-cache",
    }

response = requests.request("GET", url, headers=headers)

#Get all but the last response into the list
hooks = []
if 'Link' in response.headers:
    while 'Link' in response.headers and 'next' in response.headers['Link']:
        s = response.headers['Link']
        m = re.search(r'<.*>', s)
        link = m.group(0)[1:-1]
        res = json.loads(response.text)['items']
        for id in res:
            hooks.append(id)
        response = requests.request("GET", link, headers=headers)

#Get the last response
res = json.loads(response.text)['items']
for id in res:
    hooks.append(id)

#Delete all the webhooks
for hook in hooks:
    hookId = hook['id']
    print 'Deleting webhook for hook Id: ' + hookId
    try:
        spark.webhooks.delete(webhookId=hookId)
    except Exception as e:
        if '429' in str(e):
            sleep_time = int(e.response.headers['Retry-After'])
            if sleep_time > 60:
                sleep_time = 60
            print 'Sleeping for', sleep_time, 'seconds'
            time.sleep(sleep_time)
            spark.webhooks.delete(webhookId=hookId)
        else:
            print('Error deleting webhook for %s: %s' % (hookId, e))
            pass

#USE THIS FOR TESTING PURPOSES
#print out total number of hooks found
#variable = 0
#for item in hooks:
#    variable += 1
#    print item['id'] + ' for room ' + item['name'] + ' is hook #' + str(variable)
