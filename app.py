import os
import sys
import json

import requests
from flask import Flask, request

app = Flask(__name__)

CONST_ID = 1471279112955772

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

	if not visible(data):
		return "Não quero ver info privada dos outros users :P", 200
	sender_id = data["topic"]["details"]["created_by"]["username"]
	title = data["topic"]["title"]
	post_type = data["topic"]["archetype"]
	time = data["topic"]["last_posted_at"]
	string = "New reply from user <" + sender_id + "> on topic \"" + title + "\"\n@" + time + "\nType: " + post_type

	try:
		send_message(CONST_ID, string)
	except:
		send_message(CONST_ID, "erro :(\n Data:\n" + str(data))
	return "ok", 200

def visble(data):
	try:
		ptype = data["topic"]["archetype"]
		if ptype == "private_message":
			for user in data["topic"]["details"]["allowed_users"]:
				if user["userid"] == "Random":
					return True
			return False
		return True
	except:
		return True


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
