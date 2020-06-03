#python

import slack
import sys
import time
import re

class SlackBot(object):
    def __init__(self):
        self.debug = False
        self.api_token = None
        self.slack_client = None
        self.bot_name = None
        self.command_dictionary = []

    def debug_on(self):
        self.debug = True

    def debug_off(self):
        self.debug = False

    def debug_message(self,message):
        if self.debug:
            print(message)

    def check_slack_for_commands(self):
        self.debug_message("Checking for commands from slack")

    def set_bot_name(self, name):
        self.bot_name = str(name)

    def get_bot_name(self):
        return self.bot_name

    def connect_to_slack(self, token):
        self.api_token = str(token)
        try:
            self.slack_client = slack.WebClient(token=token)
        except:
            self.debug_message("Exception trying to connect to Slack WebClient")

        self.cache_channel_list()

    # Not thread safe, call this once at the start of the program.
    def cache_channel_list(self):
        self.channel_name_list = []
        self.channel_id_list = []
        self.debug_message("Getting channel names and IDs for caching.")
        try:
            channels = self.slack_client.channels_list()
        except:
            self.debug_message("Exception reading slack channel list.")
            return None
        self.debug_message("Total channels that exist " + str(len(channels['channels'])))

        for channel in channels['channels']:
            self.channel_name_list.append(channel['name'])
            self.channel_id_list.append(channel['id'])
            self.debug_message("Channel name: "+str(channel['name']))

    def send_message(self, msg, channels=None, file=None):
        self.debug_message("Attempting to send slack message to channel '" + str(channels) + "'")

        channel_list = None
        if channels is None:
            self.debug_message("No channel list provided for file upload")
            return
        elif isinstance(channels, str):
            channel_list = [channels]
        else:
            channel_list = channels

        channel_list_str = ""
        for i in channel_list:
            if channel_list_str == "":
                channel_list_str = str(i)
            else:
                channel_list_str = "," + str(i)

        if self.bot_name is not None and self.slack_client is not None:
            self.debug_message("Attempting to send slack message: " + str(msg))
            final_msg = self.bot_name + ": " + str(msg)

            if file is None:
                if channels is None:
                    self.debug_message("No channels given for this message.")
                else:
                    for channel in channel_list:
                        if channel in self.channel_name_list:
                            self.debug_message("Sending slack message to #" + str(channel))
                            response = None
                            try:
                                response = self.slack_client.chat_postMessage(channel='#' + channel, text=final_msg)
                            except:
                                self.debug_message("Exception sending message to channel. " + str(sys.exc_info()))
                        else:
                            self.debug_message("'" + str(channel)+"' is not a channel.  Maybe it is a handle?")
                            try:
                                response = self.slack_client.chat_postMessage(channel='@' + channel, text=final_msg)
                            except:
                                self.debug_message("Exception sending message to handle. " + str(sys.exc_info()))
            else:
                self.upload_file(file, final_msg, channels)
        else:
            if self.bot_name is None:
                self.debug_message("Cannot send slack message since bot name is not set.")
            if self.slack_client is None:
                self.debug_message("Cannot send slack message since connection to slack is not established.")

    def upload_file(self, file, msg="", channels=None):
        channel_list = None
        if channels is None:
            self.debug_message("No channel list provided for file upload")
            return
        elif isinstance(channels, str):
            channel_list = [channels]
        else:
            channel_list = channels

        channel_list_str = ""
        for i in channel_list:
            if i in self.channel_name_list:
                if channel_list_str == "":
                    channel_list_str = str(i)
                else:
                    channel_list_str = "," + str(i)
            else:
                if channel_list_str == "":
                    channel_list_str = "@"+str(i)
                else:
                    channel_list_str = ",@" + str(i)

        self.debug_message("Attempting to upload file " + str(file) + " to channels '" + channel_list_str + "'")
        try:
            self.slack_client.files_upload(
                channels=channel_list_str,
                file=file,
                initial_comment=self.bot_name + ": " + str(msg),
            )
        except:
            self.debug_message("Error trying to upload file to Slack: " + str(sys.exc_info()))

    def add_reaction_to_message(self, channel_name, timestamp):
        str_channel_name = str(channel_name)
        channel_id = self.get_channel_id_by_name(str_channel_name)
        self.debug_message("Attempting to add reaction to message from " + str_channel_name)
        if channel_id is None or channel_id is False:
            self.debug_message("Unable to add reaction to message from " + str_channel_name)
            return False
        try:
            self.slack_client.reactions_add(channel=channel_id, timestamp=timestamp, name="thumbsup")
        except:
            print("Exception adding reaction")
            self.debug_message("\n\nException when adding reaction to message from " + str_channel_name+ ". "+ str(sys.exc_info()))

    def get_channel_id_by_name(self, channel_name):
        # get the correct channel id
        str_channel_name = str(channel_name)

        self.debug_message("Getting channel ID for " + str_channel_name)
        self.debug_message("Total channels that exist " + str(len(self.channel_name_list)))

        try:
            channel_index = self.channel_name_list.index(str_channel_name)
            channel_id = self.channel_id_list[channel_index]
        except:
            self.debug_message("Cannot find " + str_channel_name)
            return None

        self.debug_message("Channel ID is " + str(channel_id) + " for " + str_channel_name)

        return channel_id

    def read_channel_history(self, channel_name, start_time=0, end_time=None):
        str_channel_name = str(channel_name)
        try:
            channel_id = self.get_channel_id_by_name(str_channel_name)
        except:
            self.debug_message("Exception trying to read channel from Slack " + str_channel_name)
            return False

        if channel_id is None:
            self.debug_message("Unable to read message history from " + str_channel_name)
            return False
        if end_time is None:
            end_time = int(time.time())

        self.debug_message("Attempting to read message history from " + str_channel_name)
        try:
            history = self.slack_client.channels_history(channel=channel_id, oldest=start_time, latest=end_time)
        except:
            self.debug_message(
                "Exception trying to read channel history from Slack for channel ID" + str(channel_id))
            return False
        self.debug_message("Finished reading messages.  Raw JSON: "+str(history))

        self.debug_message("\nIndividual messages:")
        for message in history['messages']:
            self.debug_message("\nMessage text: " + str(message['text'].lower()))
            if "reactions" not in message:
                if self.match_action(channel_name,message['text']):
                    self.debug_message("Acknowledging receipt of command '" + str(message) + "' at timestamp "
                                         + str(time.asctime(time.localtime(float(message['ts'])))))
                    self.add_reaction_to_message(channel_name, message['ts'])
            else:
                self.debug_message("Message has reaction, so not doing anything with it.")

        return history

    def set_action(self,regex,action):
        self.command_dictionary.append((regex,action))

    def match_action(self,channel, msg):
        self.debug_message("Searching for matching action for message '"+str(msg)+"' from channel")
        for (i,j) in self.command_dictionary:
            if re.search(i, msg.lower()):
                self.debug_message("Found matching action")
                j(self,channel,msg)
                return True
        return False


