from chalice import Chalice, Cron
from datetime import datetime, timedelta
from chalicelib.utils import *
# Using the Warrant package to handle generating correct SRP_A value
from warrant import Cognito


import csv
import os
import requests

app = Chalice(app_name='reinvent_bot_lambda')

@app.schedule(Cron("0", "*", "*", "*", "?", "*"))
def handler(event):
    BOT_MODE = os.getenv('REINVENT_BOT_MODE', 'False')
    BOT_MODE = True if BOT_MODE == 'True' else False

    TWEET = os.getenv('REINVENT_TWEET', 'False')
    TWEET = False if TWEET == 'True' else False

    bot = ReinventBot() if BOT_MODE else ""

    u = Cognito(
        COGNITO_POOL_ID, 
        COGNITO_CLIENT_ID,
        username=AWS_EVENTS_USERNAME, 
        user_pool_region="us-east-1"
    )
    u.authenticate(password=AWS_EVENTS_PASSWORD)

    url = "https://api.us-east-1.prod.events.aws.a2z.com/attendee/graphql"

    # Authentication token for accessing the GraphQL endpoint
    headers = {
        "Authorization": u.access_token,
    }

    # GraphQL query, 100 at a time, for AWS re:Invent sessions
    body = {
        "operationName": "ListSessions",
        "variables": {
            "input": {
                "eventId": "b84dca69-6995-4e60-bc3f-7bb7a6d170d1",
                "maxResults": 100,
            }
        },
        "query": "query ListSessions($input: ListSessionsInput!) {\n  listSessions(input: $input) {\n    results {\n      ...SessionFieldFragment\n      isConflicting {\n        reserved {\n          eventId\n          sessionId\n          isPaidSession\n          __typename\n        }\n        waitlisted {\n          eventId\n          sessionId\n          isPaidSession\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    totalCount\n    nextToken\n    __typename\n  }\n}\n\nfragment SessionFieldFragment on Session {\n  action\n  alias\n  createdAt\n  description\n  duration\n  endTime\n  eventId\n  isConflicting {\n    reserved {\n      alias\n      createdAt\n      eventId\n      name\n      sessionId\n      type\n      __typename\n    }\n    waitlisted {\n      alias\n      createdAt\n      eventId\n      name\n      sessionId\n      type\n      __typename\n    }\n    __typename\n  }\n  isEmbargoed\n  isFavoritedByMe\n  isPaidSession\n  isPaidSession\n  level\n  location\n  myReservationStatus\n  name\n  sessionId\n  startTime\n  status\n  type\n  capacities {\n    reservableRemaining\n    waitlistRemaining\n    __typename\n  }\n  customFieldDetails {\n    name\n    type\n    visibility\n    fieldId\n    ... on CustomFieldValueFlag {\n      enabled\n      __typename\n    }\n    ... on CustomFieldValueSingleSelect {\n      value {\n        fieldOptionId\n        name\n        __typename\n      }\n      __typename\n    }\n    ... on CustomFieldValueMultiSelect {\n      values {\n        fieldOptionId\n        name\n        __typename\n      }\n      __typename\n    }\n    ... on CustomFieldValueHyperlink {\n      text\n      url\n      __typename\n    }\n    __typename\n  }\n  package {\n    itemId\n    __typename\n  }\n  price {\n    currency\n    value\n    __typename\n  }\n  room {\n    name\n    venue {\n      name\n      __typename\n    }\n    __typename\n  }\n  sessionType {\n    name\n    __typename\n  }\n  tracks {\n    name\n    __typename\n  }\n  __typename\n}\n"
    }

    next_token = True
    sessions = []

    # Loop through each set of 100 sessions
    while next_token:
        print("Getting sessions...")
        response = requests.post(
            url,
            headers=headers,
            json=body,
        )
        response_data = response.json()
        print("    Total Returned:", len(response_data["data"]["listSessions"]["results"]))
        sessions = sessions + response_data["data"]["listSessions"]["results"]

        if "nextToken" in response_data["data"]["listSessions"] and response_data["data"]["listSessions"]["nextToken"] is not None:
            next_token = True
            #print("    Next Token:", response_data["data"]["listSessions"]["nextToken"])
            body["variables"]["input"]["nextToken"] = response_data["data"]["listSessions"]["nextToken"]
        else:
            next_token = False

    if not BOT_MODE:
        # Open a blank text file to write sessions to
        sessions_file = open("sessions.csv","w")
        sessions_writer = csv.writer(sessions_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        sessions_writer.writerow([
            "Session Number", 
            "Session Title", 
            "Session Interest", 
            "Start Time", 
            "End Time", 
            "Room and Building"
        ])

    for session in sessions:
        session_number = session["alias"]
        session_name = session["name"]
        venue_name = session['room']['venue']['name'] if session['room']['venue'] is not None else ""
        room_name = session['room']['name'] if session['room']['name'] is not None else ""
        room_building = f"{venue_name} - {room_name}"
        if session["startTime"] is not None:
            start_time = datetime.fromtimestamp(session["startTime"]/1000)
            end_time = start_time + timedelta(minutes=session["duration"])
            start_time = start_time.strftime("%b %d, %Y, %I:%M %p")
            end_time = end_time.strftime("%b %d, %Y, %I:%M %p")
        else:
            start_time = "0"
            end_time = "0"
        session_info = {
            "session_number": session_number,
            "session_title": session_name,
            "start_time": start_time,
            "end_time": end_time,
            "room_building": room_building,
        }
        print(session_number, session_name, start_time, end_time)
        # If we're running in BOT mode, we should handle storing the sessions
        # and tweeting out updates.
        if BOT_MODE:
            new = bot.check_if_new(str(session_number))
            # If the session is not new and I can't get the session timing,
            # I have no way to verify if the session is updated. Exit the loop
            # and continue onwards.
            if (new == False and start_time == 0):
                continue

            if (new == True):
                if ("embargo" not in session_name and not session["isEmbargoed"]):
                    session_info['version'] = "1"
                    bot.store_session(session_info)
                    if TWEET:
                        tweet = "NEW AWS #reInvent session: {!s} - {!s}".format(session_info['session_number'], \
                            session_info['session_title'])
                        print(tweet)
                        status = bot.send_tweet(tweet)
                        print(status)
            else:
                update, what_changed = bot.check_if_updated(str(session_number), session_info)
                if (update != False):
                    print("Session exists in table but needs to be updated!")
                    session_info['version'] = str(update)
                    bot.store_session(session_info)

                    if TWEET:
                        tweet = "UPDATED {!s} for #reInvent session: {!s} - {!s}".format(what_changed, \
                            session_info['session_number'], session_info['session_title'])
                        print(tweet)
                        status = bot.send_tweet(tweet)
                        print(status)

        # If we're not in BOT mode, we should write to a file.
        elif not BOT_MODE:
            if (session["isFavoritedByMe"] == False):
                session_interest = False
            else:
                session_interest = True

            sessions_writer.writerow([
                session_number, 
                session_name, 
                session_interest, 
                start_time, 
                end_time, 
                room_building
            ])

    if not BOT_MODE:
        sessions_file.close()
