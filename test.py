#python

import slackbot as sb
import os
import time
import re

def say_phrase(slacker,channel,msg):
    print("Running say_phrase()")
    match=re.search("^say (.*)$", msg.lower())
    if match is not None:
        slacker.send_message(match[1],channel)

slacker = sb.SlackBot()
slacker.debug_on()
slacker.set_bot_name(os.environ['SLACK_BOT_NAME'])
slacker.connect_to_slack(os.environ['SLACK_TOKEN'])
slacker.set_action("^say",say_phrase)
channel=os.environ['SLACK_CHANNEL']

while true:
    history = slacker.read_channel_history(channel, start_time=int(time.time()) - 600)
    if history is False:
        slacker.debug_message("There was a problem reading the history from Slack")
        exit(-1)
    if history is None:
        slacker.debug_message("There were no messages in the history returned from the Slack")
        exit(-1)
    time.sleep(5)