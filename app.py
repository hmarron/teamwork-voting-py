import mysql.connector
import logging
from flask import Flask
from flask_cors import CORS
from flask import request
import requests
import os.path
from os import path
import json
import threading

app = Flask(__name__)
CORS(app)

CLIENT_ID = ""
CLIENT_SECRET = ""
DB_IP = ""
DB_USER = ""

HELP_MSG = """
Only 1 poll can run at a given time on a channel.
If another poll is created, the old one can no longer be viewed with /poll and all votes now go to the created poll.

Commands:
**/create-poll This is the question? : Answer 1 : Answer 2 : Answer 3**
**/poll** Shows the running totals of the current poll in the channel
**/vote <number>** Where number is one of the options listed in /poll
"""

def main():
    global db

    db = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="polls"
    )

    # This is a hack
    # I can need ssl enabled to install the app,
    # but webhooks don't work with self signed cert, but they do work without ssl.
    # So running 2 flask threads one with ssl and one without.
    httpServer = threading.Thread(target=run_http)
    httpsServer = threading.Thread(target=run_https)
    httpServer.start()
    httpsServer.start()

    httpServer.join()
    httpsServer.join()

def run_http():
    app.run(port=80, host='0.0.0.0')

def run_https():
    app.run(ssl_context='adhoc', port=443, host='0.0.0.0')


@app.route('/auth')
def auth():
    data = {
        "code": request.args.get('code'),
        "client_id": CLIENT_ID,
        "redirect_uri": "https://ec2-34-245-115-217.eu-west-1.compute.amazonaws.com/auth",
        "client_secret": CLIENT_SECRET
    }
    headers = {'content-type': 'application/json'}

    r = requests.post(url = "https://twtest.teamwork.com/launchpad/v1/token.json", data=data)
    response = r.json()

    bearerToken = response["access_token"]
    installationID = response["installation"]["id"]

    set_installation_token(installationID, bearerToken)

    return 'Installed :)'

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    command = data["event"]["data"]["command"]["trigger"]
    text = data["event"]["data"]["command"]["text"]
    channelId = data["event"]["data"]["conversation"]["id"]
    userId = data["event"]["data"]["actor"]["id"]
    responseUrl = data["event"]["data"]["responseUrl"]
    installationId = data["siteId"]

    if command == "create-poll":
        args = text.split(":")
        question = args[0].strip()
        answers = args[1:]

        pollId = create_poll(question,channelId,userId)
        add_choices(pollId, answers)
        pollInfo = get_poll(pollId)

        token = get_installation_token(installationId)
        post_message(channelId, responseUrl, pollInfo, False, token)

    elif command == "poll":
        pollId = get_channel_poll_id(channelId)
        pollInfo = get_poll(pollId)
        token = get_installation_token(installationId)
        post_message(channelId, responseUrl, pollInfo, False, token)


    elif command == "vote":
        pollId = get_channel_poll_id(channelId)
        cast_vote(pollId, userId, text)

        pollInfo = get_poll(pollId)
        token = get_installation_token(installationId)
        post_message(channelId, responseUrl, pollInfo, True, token)

    elif command == "poll-help":
        token = get_installation_token(installationId)
        post_message(channelId, responseUrl, HELP_MSG, True, token)

    return "ok"

def post_message(channelId, url, text, hidden, token):
    vis = "persistent"
    if hidden:
        vis = "transient"
    data = {
        "message": {
            "visibility": vis,
            "conversationId": channelId,
            "body": text
        }
    }
    headers = {
        "content-type": "application/json",
        "Authorization": "Bearer " + token,
    }

    r = requests.post(url=url, data=json.dumps(data), headers=headers)
    response = r.json()
    print(response)
    return


######################
# User commands
######################
def create_poll(question, channelId, createdBy):
    cursor = db.cursor()

    # create poll
    sql = "INSERT INTO polls (question, channelId, createdBy) VALUES (%s, %s, %s)"
    val = (question, channelId, createdBy)

    try:
        cursor.execute(sql, val)
        db.commit()
    except Exception as e:
        logging.error(e)
        return

    return cursor.lastrowid


def get_channel_poll_id(channelId):
    cursor = db.cursor()
    sql = "SELECT id FROM polls WHERE channelId = "+str(channelId)+" ORDER BY createdAt DESC LIMIT 1"
    try:
        cursor.execute(sql)
        return cursor.fetchone()[0]
    except Exception as e:
        logging.error(e)
        return

# If bad choice, log error and do nothing.
def cast_vote(pollId, userId, pollChoiceId):
    cursor = db.cursor()

    # get choice id from pollchoiceId
    sql = "SELECT id FROM choices WHERE pollId = %s AND pollChoiceId = %s"
    val = (pollId, pollChoiceId)
    try:
        cursor.execute(sql, val)
        choiceId = cursor.fetchone()[0]
    except Exception as e:
        logging.error("failed to get choice")
        logging.error(e)
        return

    # delete existing vote
    sql = "DELETE FROM votes WHERE pollId = %s AND userId = %s"
    val = (pollId, userId)
    try:
        cursor.execute(sql, val)
        db.commit()
    except Exception as e:
        logging.error("failed to delete old vote")
        logging.error(e)
        return

    # insert vote
    sql = "INSERT INTO votes (pollId, userId, choiceId) VALUES (%s, %s, %s)"
    val = (pollId, userId, choiceId)
    try:
        cursor.execute(sql, val)
        db.commit()
    except Exception as e:
        logging.error("failed to add new vote")
        logging.error(e)
        return

    return

def add_choices(pollId, answers):
    cursor = db.cursor()
    for i in range(len(answers)):
        sql = "INSERT INTO choices (pollId, answer, pollChoiceId) VALUES (%s, %s, %s)"
        val = (pollId, answers[i].strip(), i+1)

        try:
            cursor.execute(sql, val)
            db.commit()
        except Exception as e:
            logging.error(e)
            return

def remove_choice(pollId, pollChoiceId):
    cursor = db.cursor()
    sql = "DELETE FROM choices WHERE pollId = %s AND pollChoiceId = %s"
    val = (pollId, pollChoiceId)

    try:
        cursor.execute(sql, val)
        db.commit()
    except Exception as e:
        logging.error(e)
        return

def get_poll(pollId):
    cursor = db.cursor()
    sql = "SELECT choices.answer, COUNT(votes.id) FROM choices LEFT JOIN votes ON choices.id = votes.choiceId WHERE choices.pollId = "+str(pollId)+" GROUP BY choices.id"
    try:
        cursor.execute(sql)
        result = cursor.fetchall()
    except Exception as e:
        logging.error(e)
        return

    return_str = ""
    for i in range(len(result)):
        return_str += str(i+1) + ": " + result[i][0] + ": " + str(result[i][1]) + "\n"

    return return_str

def get_installation_token(installationID):
    cursor = db.cursor()
    sql = "SELECT token FROM installation_tokens WHERE installationId = " + str(installationID)
    try:
        cursor.execute(sql)
        return cursor.fetchone()[0]
    except Exception as e:
        logging.error(e)
        return

def set_installation_token(installationID, token):
    cursor = db.cursor()

    # delete existing token
    sql = "DELETE FROM installation_tokens WHERE installationId = " + str(installationID)
    try:
        cursor.execute(sql)
        db.commit()
    except Exception as e:
        logging.error(e)
        return

    # insert token
    sql = "INSERT INTO installation_tokens (installationId, token) VALUES (%s, %s)"
    val = (installationID, token)
    try:
        cursor.execute(sql, val)
        db.commit()
    except Exception as e:
        logging.error(e)
        return

def clear():
    cursor = db.cursor()
    clear_commands = ["DELETE FROM votes", "DELETE FROM choices", "DELETE FROM polls"]
    for sql in clear_commands:
        try:
            cursor.execute(sql)
            db.commit()
        except Exception as e:
            logging.error(e)
            return

if __name__ == "__main__":
    main()

