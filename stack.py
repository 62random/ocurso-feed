# -*- coding: utf-8 -*-
import sys
import json
from bs4 import BeautifulSoup
import re
from pydiscourse import DiscourseClient
import gspread
from oauth2client.service_account import ServiceAccountCredentials

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

############################### LOGGING ########################################

logging.basicConfig(filename='stack.log', level=logging.INFO)
log = logging.getLogger(__name__)


############################### CONSTANTES #####################################
ENGRACADINHOS = ['18_19']
MANOS = ['Random', 'Stack']

################################################################################
#abrir ficheiro de teste //retirar depois
with open("data.json", "r") as file:
    data = json.load(file)


#retirar as mentions do texto
def get_mentions(cooked):
    soup = BeautifulSoup(cooked, 'html.parser')
    list = []
    for i in soup.find_all('a'):
        if(i['class'][0] == "mention" and i.get_text().encode() in ENGRACADINHOS):          #o [0] e para extrair a string "mention" do objeto
            list.append(i.get_text().encode())
    return list

#processa a mensagem e retira o número a adicionar à stack
def number_cooked(cooked):
    soup = BeautifulSoup(cooked, 'html.parser')
    str = soup.get_text()
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
                mensagem = mensagem + '     ' + a + ' +' + str(number) + ' ->  ' + str(dict[a])
            responde(data, mensagem)
        write_sheet(dict, wks)
