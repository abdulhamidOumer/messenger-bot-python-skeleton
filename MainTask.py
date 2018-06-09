import os
import sys
import json
import requests
from datetime import datetime
import urlparse
import random


from flask import Flask , request


app = Flask(__name__)


@app.route('/',methods=['GET'])
def handleIncomingGet():
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
        if not request.args.get("hub.verify_token") == os.environ["MY_TOKEN"]:
            return "Verification token Mismatch", 403
        return request.args["hub.challenge"], 200
    return "Simple Text", 200


@app.route('/', methods=['POST'])
def handleIncomingPost():
    payload = request.get_data()
    data = json.loads(payload)
    log(data)
    messaging_events = data["entry"][0]["messaging"]

    for event in messaging_events:
        if "message" in event and "text" in event["message"] and "quick_reply" not in event["message"]:  # Handle incoming text messages
            sender_id = event["sender"]["id"]
            messages = event["message"]["text"].encode('unicode_escape')

            handle_incoming_text(sender_id, messages)

        elif "message" in event and "quick_reply" in event["message"]:  # Handle incoming quick replies
            payload = event["message"]["quick_reply"]["payload"].encode('unicode_escape')
            text = event["message"]["text"].encode('unicode_escape')
            sender = event["sender"]["id"]
            handle_quick_replies(payload, text, sender)

        elif "postback" in event and "payload" in event["postback"]:  # Handle incoming postback results
            payload = event["postback"]["payload"].encode('unicode_escape')
            sender = event["sender"]["id"]
            handle_incoming_postbacks(payload, sender)

        elif "message" in event and "attachments" in event["message"]:  # Handle incoming attachment messages

            if event['message']['attachments'][0]["type"] == 'location': # When attachment is location
                cordinates = event['message']['attachments'][0]['payload']['coordinates']
                lat = cordinates['lat']
                long = cordinates['long']

            elif event['message']['attachments'][0]["type"] == 'image':  # When attachment is image
                imageURL = str(event['message']['attachments'][0]['payload']['url'])

            else:
                send_text_message(event["sender"]["id"], "I can't handle this attachment yet")

        else:
            send_text_message(event["sender"]["id"], "I can't handle this kind of messages yet")

    return "OK",200


def send_text_message(user_id, message_text):

    log("sending message to {recipient}: {text}".format(recipient=user_id, text=message_text))

    params = {
        "access_token": os.environ["PAGE_ACCESS_TOKEN"]
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = json.dumps({
        "recipient": {
            "id": user_id
        },
        "message": {
            "text": message_text
        }
    })
    r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)
    if r.status_code != 200:
        log(r.status_code)
        log(r.text)


def send_templates(user_id, elements, template_type = "generic"):
    params = {
        "access_token": os.environ["PAGE_ACCESS_TOKEN"]
    }
    headers = {
        "Content-Type": "application/json"
    }

    data = json.dumps({
        "recipient": {
            "id": user_id
        },
        "message": {
            "attachment": {
                "type": "template",
                "payload": {
                    "template_type": template_type,
                    "elements": elements
                }
            }
        }
    })
    r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)
    if r.status_code != 200:
        log(r.status_code)
        log(r.text)


def send_quick_replies(user_id, message, elements):
    params = {
        "access_token": os.environ["PAGE_ACCESS_TOKEN"]
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = json.dumps({
        "recipient": {
            "id": user_id
        },
        "message": {
            "text": message,
            "quick_replies": elements
        }
    })
    r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)
    if r.status_code != 200:
        log(r.status_code)
        log(r.text)


def send_buttoned_messages(user_id,message,elements):
    params = {
        "access_token": os.environ["PAGE_ACCESS_TOKEN"]
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = json.dumps({
        "recipient": {
            "id": user_id
        },
        "message": {
            "attachment": {
                "type": "template",
                "payload": {
                    "template_type": "button",
                    "text": message,
                    "buttons": elements
                }}}})
    r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)
    if r.status_code != 200:
        log(r.status_code)
        log(r.text)



def send_attachment(user_id, file_types, url):
    params = {
        "access_token": os.environ["PAGE_ACCESS_TOKEN"]
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = json.dumps({
        "recipient":{
    "id":user_id
       },
    "message":{
    "attachment":{
      "type":file_types,
      "payload":{
        "url":url
      }
    }
  }
    })
    r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)
    if r.status_code != 200:
        log(r.status_code)
        log(r.text)



def set_persistant_menu():
    params = {
        "access_token": os.environ["PAGE_ACCESS_TOKEN"]
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = json.dumps({
    "persistent_menu":[
    {
      "locale":"default",
      "composer_input_disabled":False,
      "call_to_actions":[
        {
            "title":"\xF0\x9F\x93\x96 See A Menu",
            "type":"postback",
            "payload":"SEE-MENU"
        },
          {
              "title": "\xF0\x9F\x8D\xB4 Order A Food",
              "type": "postback",
              "payload": "ORDER-FOOD"
          }
      ]
    }
    ]
    })

    r = requests.post("https://graph.facebook.com/v2.6/me/messenger_profile", params=params, headers=headers, data=data)
    print "Persistant " + r.text
    if r.status_code != 200:
        log(r.status_code)
        log(r.text)


def set_whitelist_domains():

    params = {
        "access_token": os.environ["PAGE_ACCESS_TOKEN"]
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = json.dumps({
         "whitelisted_domains":[
            "https://google.com"   #Add The Website domains of links you will send to your bot user

        ]
    })

    r = requests.post("https://graph.facebook.com/v2.6/me/messenger_profile", params=params, headers=headers, data=data)

    log(r.status_code)
    log(r.text)
    print "White listed Domains!!"


def set_greeting_text(text):    ## Set a greeting text to user that will be visible before sending message
    params = {
        "access_token": os.environ["PAGE_ACCESS_TOKEN"]
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = json.dumps({
        "greeting":[
        {
            "locale":"default",
            "text": text
         }
       ]
    })

    r = requests.post("https://graph.facebook.com/v2.6/me/messenger_profile", params=params, headers=headers, data=data)
    if r.status_code != 200:
        log(r.status_code)
        log(r.text)


def set_get_started_button():  ## Set a get started button, that's avialable the first time user makes contact
    params = {
        "access_token": os.environ["PAGE_ACCESS_TOKEN"]
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = json.dumps({
        "get_started":{
            "payload":"GET_STARTED"
     }
        }
    )

    r = requests.post("https://graph.facebook.com/v2.6/me/messenger_profile", params=params, headers=headers, data=data)
    if r.status_code != 200:
        log(r.status_code)
        log(r.text)


def log(message):  # simple wrapper for logging to stdout on heroku
    print str(message)
    sys.stdout.flush()


def handle_incoming_text(sender_id, message):
   response = "User said: "+message
   send_text_message(sender_id, response)
   log(response)


def handle_incoming_postbacks(payload, sender):
    print "Recieved: a {0} payload".format(payload)


def handle_quick_replies(payload,text, sender):
    print "Recieved a {0} payload and a text {1}".format(payload,text)




if __name__ == '__main__':
    app.run(debug=True)
