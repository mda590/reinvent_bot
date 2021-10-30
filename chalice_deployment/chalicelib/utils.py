from .config import *

import boto3
import twitter

class ReinventBot():
    def __init__(self):
        self.dynamodb = boto3.client('dynamodb', region_name='us-east-2')
        self.table_name = SESSION_TABLE
        self.api = self._connect_to_twitter()

    def check_if_new(self, session_number):
        if (self._get_stored_session(session_number) == 1):
            # If there is no session stored in DB with the same ID, return True, this is a new session
            return True  
        else:
            # If there is a match in the DB with the same ID, return False, this is not new
            return False

    def check_if_updated(self, session_number, new_session_info):
        is_updated = False
        what_changed = ''
        response = self._get_stored_session(session_number)
        if (response != 1):
            session_number = response['Items'][0]['session_number']['S']
            if (session_number == new_session_info['session_number']):
                version = response['Items'][0]['version']['N']
                session_title = response['Items'][0]['session_title']['S']
                start_time = response['Items'][0]['start_time']['S']
                if start_time != new_session_info['start_time']:
                    is_updated = True
                    what_changed = what_changed + "Start Time, "
                else:
                    is_updated = False
                end_time = response['Items'][0]['end_time']['S']
                if end_time != new_session_info['end_time']:
                    is_updated = True
                    what_changed = what_changed + "End Time, "
                else:
                    is_updated = False
                room_building = response['Items'][0]['room_building']['S']
                if room_building != new_session_info['room_building']:
                    is_updated = True
                    what_changed = what_changed + "Room or Building, "
                else:
                    is_updated = False

        if (is_updated):
            what_changed = what_changed[:-2]
            return (int(version) + 1), what_changed
        else:
            return False, False

    def _get_stored_session(self, session_number):
        # Find all records in DB with session_number
        # Set ScanIndexForward to False to return results sorted in desc order on version
        response = self.dynamodb.query(
            ExpressionAttributeValues={
                ':v1': {
                    'S': session_number,
                },
            },
            KeyConditionExpression='session_number = :v1',
            ScanIndexForward=False,
            TableName=self.table_name,
        )
        if (response['Count'] > 0):
            return response
        else:
            return 1

    def store_session(self, session_info):
        response = self.dynamodb.put_item(
            Item={
                "session_number": {
                    'S': session_info['session_number']
                },
                "version": {
                    'N': session_info['version']
                },
                "session_title": {
                    'S': session_info['session_title']
                },
                "start_time": {
                    'S': session_info['start_time']
                },
                "end_time": {
                    'S': session_info['end_time']
                },
                "room_building": {
                    'S': session_info['room_building']
                }
            },
            TableName=self.table_name)

    def _connect_to_twitter(self):
        api = twitter.Api(
            consumer_key=MY_CONSUMER_KEY,
            consumer_secret=MY_CONSUMER_SECRET,
            access_token_key=MY_ACCESS_TOKEN_KEY,
            access_token_secret=MY_ACCESS_TOKEN_SECRET)
        return api

    def send_tweet(self, tweet):
        tweet = self._process_tweet(tweet)
        status = self.api.PostUpdate(tweet)
        return status.text.encode('utf-8')

    def _process_tweet(self, tweet):
        tweet = (tweet[:125] + '...') if len(tweet) > 140 else tweet
        return tweet

