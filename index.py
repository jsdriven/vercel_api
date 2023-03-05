from flask import Flask, render_template, Response
from urllib.request import urlopen
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import json
import time
import queue



app=Flask(__name__)

global scores 
scores = {}

class dataQueue:

    def __init__(self):
        self.listeners =[]

    def listen(self):
        listener = queue.Queue(maxsize=5)
        self.listeners.append(listener)
        print(f'Listener added. Current amount: {len(self.listeners)}')
        return listener

    def post(self, msg: str):
        msgString = f'{msg}\n\n'
        for i in range(len(self.listeners)):
            try:
                self.listeners[i].put_nowait(msgString)
            except queue.Full:
                print(f'Queue {i} full. Deleting.')
                del self.listeners[i]

    def getPost(self):
        return self.q.get()
    
    def getCurrent(self):
        return scores
    
    def removeListener(self, q: queue):
        print("Removing listener")
        try:
            self.listeners.remove(q)
            print(f'Listeners remaining {len(self.listeners)}')
        except:
            print("Issue removing listener queue.")

data = dataQueue()

#@app.route('/getnbascores')
def getnbascores():
    print(f'Getting scores from espn.')
    response = urlopen('http://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard')
    jObject = json.loads(response.read())
    events = jObject["events"]
    formattedEvents = list(map(mapGameInfo, events))
    global scores
    scores = formattedEvents
    data.post(formattedEvents)
    
## This needs to be updated to point to espn data
def scheduledAction(d: dataQueue):
    d.post("This is a test msg")
    print("Message added")
    return


scheduler = BackgroundScheduler()
print("STARTING")
#scheduler.add_job(scheduledAction, 'interval',args=[data], seconds=30)
#scheduler.add_job(getnbascores, CronTrigger.from_crontab('*/5 0-2,12-23 * * *'))
try:
    scheduler.start()
except (KeyboardInterrupt):
    print('Got SIGTERM! Terminating...')

@app.route('/')
def home():
    return 'Home Page'

def streamTest():
    try:
        print("Connected")
        messsages = data.listen()
        while True:
            msg = messsages.get()
            yield msg
    finally:
        data.removeListener(messsages)
        print("Disconnected")

@app.route('/scoreUpdates')
def test():
    return Response(
        streamTest(),
        mimetype='text/event-stream'
    )

@app.route('/currentScores')
def getCurrentScores():
    return scores

def mapGameInfo(event):
    state = event["status"]["type"]["description"]
    if(state == "Scheduled"): 
        return {
            "team1": event["competitions"][0]["competitors"][0]["team"]["abbreviation"],
            "team2": event["competitions"][0]["competitors"][1]["team"]["abbreviation"],
            "state": event["status"]["type"]["description"],
            "stateDetail": event["status"]["type"]["shortDetail"]
        }
    else:
        return {
        "team1": event["competitions"][0]["competitors"][0]["team"]["abbreviation"],
        "team1score": event["competitions"][0]["competitors"][0]["score"],
        "team2": event["competitions"][0]["competitors"][1]["team"]["abbreviation"],
        "team2score": event["competitions"][0]["competitors"][1]["score"],
        "state": event["status"]["type"]["description"],
        "stateDetail": event["status"]["type"]["shortDetail"]
    }




    
    ## ## This uses the other url through script tag rather than the hidden api
    ## This gives us all the data we need for the scores - we really dont even need the ui anymore this is json of all the scores and data
    ##url = requests.get('https://www.espn.com/nba/scoreboard')
    ##soup = BeautifulSoup(url.text, "lxml")
    ##scrapt_tag = soup.find_all("script", src=None)
    ##pattern = "window['__espnfitt__']="
    ##raw_data_first = scrapt_tag[1].string.split(pattern)[1]
    ##raw_data = raw_data_first.rstrip(raw_data_first[-1])
    ##f = open("dump.json","a")
    ##f.write(raw_data)
    ##f.close()
    ##json_data = json.loads(raw_data)       
    ##events = json_data["page"]["content"]["scoreboard"]["evts"]
    ##retval = list(map(mapGameInfo, events))
    ##return list(retval)