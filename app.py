# -*- coding: utf-8 -*-
import os
import sys
import json
import re
import HTMLParser
import requests
from flask import Flask, request
import constantids
from bs4 import BeautifulSoup
from pydiscourse import DiscourseClient
import gspread
from oauth2client.service_account import ServiceAccountCredentials
app = Flask(__name__)

################################################################################
################################################################################
################# STACK ########################################################
################################################################################
#################### AUTENTICAR SERVICOS GOOGLE ################################

SCOPE = [ 'https://www.googleapis.com/auth/drive']

CREDENTIALS = ServiceAccountCredentials.from_json_keyfile_name('creds.json',SCOPE)

gc = gspread.authorize(CREDENTIALS)

wks = gc.open('Stack').sheet1

###################### API DO DISCOURSE ########################################

client_stack = DiscourseClient(
            'https://ocurso.org',
            api_username='Stack',
            api_key='888c97246374bc65ee74281ed797de4ca51fe00700f3afe3184efdd98a74a6c0')

############################### CONSTANTES #####################################
ENGRACADINHOS = ['18_19']
MANOS = ['Random', 'Stack']

################################################################################

#retirar as mentions do texto
def get_mentions(cooked):
    soup = BeautifulSoup(cooked, 'html.parser')
    list = []
    flag = False
    for i in soup.find_all('a'):
        if 'Stack' in i.get_text().encode():
            flag = True
        if i['class'][0] == "mention" and not 'Stack' in i.get_text().encode():          #o [0] e para extrair a string "mention" do objeto
            list.append(i.get_text().encode())
    if flag:
        return list
    else:
        return []

#processa a mensagem e retira o número a adicionar a stack
def number_cooked(cooked):
    soup = BeautifulSoup(cooked, 'html.parser')
    str = soup.get_text()
    str = str[(str.find('+')):] + ' ' + str[(str.find('-')):]
    return int(re.findall(r'-?\d+', str)[0])

#vê o grupo a que pertence um determinado user
def get_group(string):
    return client_stack.user(string)['primary_group_name']

#constrói uma mention a partir de um user
def make_mention(user):
    return '@' + user.title()

#envia uma mensagem para o discourse, sabendo os dados de um post e a resposta
def responde(data, string):
    topic = data['post']['topic_id']
    client_stack.create_post(string, topic_id= topic)

#escreve o dicionario com as stacks na spreadsheet
def write_sheet(dict, wks):
    for i in range(2):
        wks.delete_row(1)
    wks.append_row(dict.keys())
    wks.append_row(dict.values())


#flow do script
def stack(data):
    if data["post"]:                                #sacar texto da mensagem
        cooked = (data["post"]["cooked"])
    dict = {}
    for i in wks.get_all_records():
        dict.update(i)

    user = data['post']['name']                     #ver user que criou o post

    if get_group(user) in ENGRACADINHOS:            #ver se o gajo pode usar a stack
        dict[user] += 1000
        responde(data, 'Paneleiro, enche mil...\n    '+ make_mention(user) + ' +1000 -> ' + dict[user])
    else:
        number = number_cooked(cooked)
        list = get_mentions(cooked)
        mensagem = ''
        for a in list:
            try:
                dict[a] += number
            except:
                dict.update({a: number})
            mensagem = mensagem + '     ' + a + ' +' + str(number) + ' ->  ' + str(dict[a]) + '\n'

        responde(data, mensagem)
    write_sheet(dict, wks)
    return('O user ' + user + ' meteu nas stacks ' + str(dict) + ' ' + str(number))


################################################################################
################################################################################
################################################################################

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

    send_message(constantids.RANDOM, stack(data))
    '''
    try:
        facebook_message(data)
        return "ok", 200
    except:
        pass

    try:
        created_post(data)
        return "ok", 200
    except:
        pass

    try:
        created_topic(data)
        return "ok", 200
    except:
        send_message(constantids.RANDOM, "erro :(\n Data:\n" + str(data))
    '''
    return "ok", 200


def created_post(data):

	sender_id = data["post"]["username"]
	title = data["post"]["topic_title"]
	time = data["post"]["created_at"]
	time = time[11:16] + " of " + time[0:10]
	said = data["post"]["cooked"]
	string = "New reply from user [" + sender_id + "] on topic [" + title + "]\nat " + time + "\nAnd said: \n\"" + said + "\""

        if "lazyYT" in string:
            string = string.replace("<div class=\"lazyYT\" data-youtube-id=\"", "https://www.youtube.com/watch?v=")
            string = string.replace("\" data-youtube", " <div")
        string = remove_tags(string)
	send_bloco(string)

def created_topic(data):
	sender_id = data["topic"]["details"]["created_by"]["username"]
	title = data["topic"]["title"]
	post_type = data["topic"]["archetype"]
	time = data["topic"]["last_posted_at"]
	time = time[11:16] + " of " + time[0:10]
	string = "New topic [" + topic + "] created by user [" + sender_id + "]\nat " + time + ".\nType: " + post_type

	string = remove_tags(string)
	send_bloco(string)



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


def facebook_message(data):
    if data["object"] == "page":
        for entry in data["entry"]:
            try:
                for messaging_event in entry["messaging"]:

                    if messaging_event.get("message"):  # someone sent us a message

                        sender_id = messaging_event["sender"]["id"]        # the facebook ID of the person sending you the message
                        recipient_id = messaging_event["recipient"]["id"]  # the recipient's ID, which should be your page's facebook ID
                        message_text = messaging_event["message"]["text"]  # the message's text

                    if message_text != "/":
                            try:
                                send_message(constantids.RANDOM, sender_id + " said:\n\"" + message_text + "\"")
                            except:
                                send_message(constantids.RANDOM, "enche 10")

                    if messaging_event.get("delivery"):  # delivery confirmation
                        pass

                    if messaging_event.get("optin"):  # optin confirmation
                        pass

                    if messaging_event.get("postback"):  # user clicked/tapped "postback" button in earlier message
                        pass
            except:
                pass

def log(message):  # simple wrapper for logging to stdout on heroku
    print(str(message))
    sys.stdout.flush()


if __name__ == '__main__':
    app.run(debug=True)
