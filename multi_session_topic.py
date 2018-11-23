############################################################################################
#### AWS re:Invent - Session Information Downloader & Twitter Bot
# Provides a quick dirty way to export AWS re:Invent session content from the event website.
#
# Multi Topic Edition! Meant to be used standalone - will go out and get all of the 
# available re:Invent session topics, and then loop through each one, pulling session info.
#
# Requirements:
# 1. Rename config.example.py to config.py and update the variables in the file.
# 2. Download the Chrome web driver (https://sites.google.com/a/chromium.org/chromedriver/downloads).
# 3. Unzip the Chrome webdriver binary into a folder that exists in your PATH.
#
# @author Matt Adorjan
# @email matt.adorjan@gmail.com
############################################################################################

from bs4 import BeautifulSoup
from config import *
from datetime import datetime
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from time import sleep
from unidecode import unidecode
from utils import *

import json
import os
import re
import requests

BOT_MODE = True
TWEET = True

# Chrome web driver path - only required if not in PATH
# CHROME_DRIVER = './chromedriver.exe'

# Set to False to ignore SSL certificate validation in Requests package
REQ_VERIFY = True

start = datetime.now()

bot = ReinventBot() if BOT_MODE else ""

# In order to actually get all of the sessions, we need to use the filters
# Which return the viewest sessions with each request. The topic filter provides this.
r = requests.get("https://www.portal.reinvent.awsevents.com/connect/search.ww")

soup = BeautifulSoup(r.text, "html.parser")

topic_ids = []

topics = soup.find("div", id="profileItem_10240_tr")
topics = topics.find("div", class_="formContent")
topics = topics.find_all("input")
for t in topics:
    topic_ids.append(t['value'])

# Initialize headless chrome
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
content_to_parse = ''

driver = webdriver.Chrome(chrome_options=chrome_options)

def login(chrome_driver, username, password):
    '''
    Handle user login to the reinvent session catalog.
    Utilizes headless chrome, passing in username and password
    '''
    chrome_driver.get("https://www.portal.reinvent.awsevents.com/connect/login.ww")
    username_field = chrome_driver.find_element_by_id("loginUsername")
    username_field.send_keys(username)
    password_field = chrome_driver.find_element_by_id("loginPassword")
    password_field.send_keys(password)
    cookieAccept = chrome_driver.find_element_by_id( "cookieAgreementAcceptButton" )
    cookieAccept.click()    
    login_button = chrome_driver.find_element_by_id("loginButton")
    login_button.click()

def get_session_time(session_id):
    '''
    Calls the API on the reinvent event website which returns session times.
    Outputs a JSON object with time and room information for a specific session.
    '''
    url = 'https://www.portal.reinvent.awsevents.com/connect/dwr/call/plaincall/ConnectAjax.getSchedulingJSON.dwr'
    data = {
        "callCount": 1,
        "windowName": "",
        "c0-scriptName": "ConnectAjax",
        "c0-methodName": "getSchedulingJSON",
        "c0-id": 0,
        "c0-param0": "number:{}".format(session_id),
        "c0-param1": "boolean:false",
        "batchId": 6,
        "instanceId": 0,
        "page": "%2Fconnect%2Fsearch.ww",
        "scriptSessionId": "aa$GdZcE0UHnrOn2rs*Baug1rnm/JuuLapm-fcKKw5gVn"
    }
    headers = {'Content-Type': 'text/plain'}
    r = requests.post(url, headers=headers, data=data, verify=REQ_VERIFY)
    returned = r.content
    returned = returned.decode('utf-8').replace("\\", '')

    schedule_info = re.search(r"\"{\"data\": (\[.*?\])", returned, re.DOTALL | re.MULTILINE).group(1)
    time_information = {}
    try:
        schedule_info = json.loads(schedule_info)[0]

        if 'startTime' in schedule_info:
            time_information = {
                "start_time": schedule_info['startTime'],
                "end_time": schedule_info['endTime'],
                "room": schedule_info['room']
            }
        else:
            time_information = {
                "start_time": "FALSE",
                "end_time": "FALSE",
                "room": "FALSE"
            }
    except:
        time_information = {
            "start_time": "FALSE",
            "end_time": "FALSE",
            "room": "FALSE"
        }        

    return time_information

# Login to the reinvent website
login(driver, USERNAME, PASSWORD)

# Getting content by topic, instead of the entire set, because sometimes the
# Get More Results link stops working on the full list. Haven't had issues
# looking at the lists topic by topic.

driver.get("https://www.portal.reinvent.awsevents.com/connect/search.ww")
for topic in topic_ids:
    checkBox = driver.find_element_by_css_selector("input[value='{}']".format(topic))
    checkBox.location_once_scrolled_into_view
    checkBox.send_keys(Keys.SPACE)

    sleep(3)
    print ("Getting Content for Topic Code: " + str(topic))
    more_results = True

    # Click through all of the session results pages for a specific topic.
    # The goal is to get the full list for a topic loaded.
    while(more_results):
        try:
            # Find the Get More Results link and click it to load next sessions
            get_results_btn = driver.find_element_by_link_text("Get More Results")
            get_results_btn.click()
            sleep(3)
        except NoSuchElementException as e:
            more_results = False

    sleep(3)
    checkBox.send_keys(Keys.SPACE)

    # Once all sessions for the day have been loaded by the headless browser,
    # append to a variable for use in BS.
    content_to_parse = content_to_parse + driver.page_source

driver.close()

# Start the process of grabbing out relevant session information and writing to a file
soup = BeautifulSoup(content_to_parse, "html.parser")

# In some event titles, there are audio options available inside of an 'i' tag
# Strip out all 'i' tags to make this easier on BS
# Hopefully there is no other italicized text that I'm removing
for i in soup.find_all('i'):
    i.extract()

# Grab all of the sessionRows from the final set of HTML and work only with that
sessions = soup.find_all("div", class_="sessionRow")

if not BOT_MODE:
    # Open a blank text file to write sessions to
    file = open("sessions.txt","w")
    # Create a header row for the file. Note the PIPE (|) DELIMITER.
    file.write("Session Number,Session Title,Session Interest,Start Time,End Time,Room and Building\n")

# For each session, pull out the relevant fields and write them to the sessions.txt file.
for session in sessions:
    session_soup = BeautifulSoup(str(session), "html.parser")
    session_id = session_soup.find("div", class_="sessionRow")
    session_id = session_id['id']
    session_id = session_id[session_id.find("_")+1:]

    session_title = session_soup.find("span", class_="title")
    session_title = session_title.string.encode('utf-8').rstrip()
    session_title = session_title.decode('utf-8')
    #session_title = re.sub(u'[\u201c\u201d]','"',session_title)
    session_title = unidecode(session_title)

    session_timing = get_session_time(session_id)
    
    session_number = session_soup.find("span", class_="abbreviation")
    session_number = session_number.string.replace(" - ", "")

    session_abstract = session_soup.find("span", class_="abstract")

    # Print the session Number and Title
    print("{!s}: {!s}".format(session_number, session_title))

    # If we're running in BOT mode, we should handle storing the sessions
    # and tweeting out updates.
    if BOT_MODE:
        new = bot.check_if_new(str(session_number))
        # If the session is not new and I can't get the session timing,
        # I have no way to verify if the session is updated. Exit the loop
        # and continue onwards.
        if (new == False and session_timing['start_time'] == "FALSE"):
            continue

        session_info = {
            "session_number": str(session_number),
            "session_title": session_title,
            "start_time": str(session_timing['start_time']),
            "end_time": str(session_timing['end_time']),
            "room_building": str(session_timing['room'])
        }

        session_url = "https://www.portal.reinvent.awsevents.com/connect/search.ww#loadSearch-searchPhrase="+str(session_number)+"&searchType=session&tc=0&sortBy=abbreviationSort&p="

        if (new == True):
            if ("embargo" not in session_title):
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
        session_interest = session_soup.find("a", class_="interested")
        if (session_interest == None):
            session_interest = False
        else:
            session_interest = True

        write_contents = "{!s},{!s},{!s},{!s},{!s},{!s}".format(session_number, \
            session_title, session_interest, session_timing['start_time'], \
            session_timing['end_time'], session_timing['room'])
        file.write(write_contents + "\n")

if not BOT_MODE:
    file.close()

end = datetime.now()

print("Start {}".format(start))
print("End {}".format(end))
