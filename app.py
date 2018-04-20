import os
import sys
import json
import re

import requests
from flask import Flask, request

app = Flask(__name__)

CONST_ID = 1471279112955772
TAG_RE = re.compile(r'<[^>]+>')

@app.route('/', methods=['GET'])
def verify():
    # when the endpoint is registered as a webhook, it must echo back
    # the 'hub.challenge' value it receives in the query arguments
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
        if not request.args.get("hub.verify_token") == os.environ["VERIFY_TOKEN"]:
            return "Verification token mismatch", 403
        return request.args["hub.challenge"], 200

    return "Hello world", 200


@app.route('/', methods=['POST'])
def webhook():

    # endpoint for processing incoming messaging events
	data = request.get_json()
	log(data)  # you may not want to log every incoming message in production, but it's good for testing
	try:
		created_post(data)
	except:
		try:
			created_topic(data)
		except:
			send_message(CONST_ID, "erro :(\n Data:\n" + str(data))

	return "ok", 200


def created_post(data):

	try:
		sender_id = data["post"]["username"]
	except:
		sender_id = "sender_id"

	try:
		title = data["post"]["topic_title"]
	except:
		title = "title"

	try:
		time = data["post"]["created_at"]
	except:
		time = "time"

	try:
		said = remove_tags(data["post"]["cooked"])
	except:
		said = "said"

	string = "New reply from user <" + sender_id + "> on topic \"" + title + "\"\n@" + time + "\nAnd said: \n\"" + said + "\""

	send_message(CONST_ID, said)


def created_topic(data):
	sender_id = data["topic"]["details"]["created_by"]["username"]
	title = data["topic"]["title"]
	post_type = data["topic"]["archetype"]
	time = data["topic"]["last_posted_at"]
	string = "New topic \"" + topic + "\" created by user <" + sender_id + ">\n@" + time + "\nType: " + post_type

	send_message(CONST_ID, string)

def remove_tags(text):
    return TAG_RE.sub('', text)

def send_message(recipient_id, message_text):

    log("sending message to {recipient}: {text}".format(recipient=recipient_id, text=message_text))

    params = {
        "access_token": os.environ["PAGE_ACCESS_TOKEN"]
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = json.dumps({
        "recipient": {
            "id": recipient_id
        },
        "message": {
            "text": message_text
        }
    })
    r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)
    if r.status_code != 200:
        log(r.status_code)
        log(r.text)


def log(message):  # simple wrapper for logging to stdout on heroku
    print str(message)
    sys.stdout.flush()


if __name__ == '__main__':
    app.run(debug=True)
