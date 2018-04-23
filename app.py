import os
import sys
import json
import re
import HTMLParser
import requests
from flask import Flask, request
import constantids
app = Flask(__name__)

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
			send_message(RANDOM, "erro :(\n Data:\n" + str(data))

	return "ok", 200


def created_post(data):

	sender_id = data["post"]["username"]
	title = data["post"]["topic_title"]
	time = data["post"]["created_at"]
	time = time[11:16] + " of " + time[0:10]
	said = data["post"]["cooked"]
	string = "New reply from user [" + sender_id + "] on topic [" + title + "]\nat " + time + "\nAnd said: \n\"" + said + "\""

	prepstring = remove_tags(string)
	send_bloco(prepstring)

def created_topic(data):
	sender_id = data["topic"]["details"]["created_by"]["username"]
	title = data["topic"]["title"]
	post_type = data["topic"]["archetype"]
	time = data["topic"]["last_posted_at"]
	time = time[11:16] + " of " + time[0:10]
	string = "New topic [" + topic + "] created by user [" + sender_id + "]\nat " + time + ".\nType: " + post_type

	prepstring = remove_tags(string)
	send_bloco(prepstring)



def remove_tags(text):
    return TAG_RE.sub('', text)

def send_bloco(message_text):
	for recipient_id in constantids.BLOCO:
		try:
			send_message(recipient_id, message_text)
		except:
			pass

def send_message(recipient_id, message_text):

    log("sending message to {recipient}: {text}".format(recipient=recipient_id, text=message_text.encode('utf-8')))

    params = {
        "access_token": os.environ["PAGE_ACCESS_TOKEN"]
    }
    headers = {
        "Content-Type": "application/json; charset=utf-8"
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
