# AWS re:Invent Session Downloader & Twitter Bot

## This repo contains code which provides 2 pieces of functionality:
1. **Download re:Invent sessions to a text file** - The re:Invent session catalog is extremely painful to work with and with 100's of sessions offered each year, it's near impossible to use the session catalog and feel comfortable that you've seen everything you may want to attend. This script will allow you to download all of the re:Invent sessions from the catalog to a text file which you can then parse and manipulate in any way you wish.

2. **Twitter Bot** - This script stores every re:Invent session in a database and keeps track of changes to sessions by adding new records to the database with new versions. In the event that a new session is detected or there is a change to an existing session, this script will use the Twitter API to send a Tweet from the @reinvent_bot account.

The above 2 pieces of functionality work independently of each other and can be toggled on/off by changing a few variables.

## These are 2 separate Python files which perform similar functionality, but achieved different ways:
1. `multi_session_topic.py` - First scrapes the re:Invent catalog to get all of the available session topics from the topics listed in the filters on the left-hand side. Once we have a list of topic IDs, we loop through each topic ID and then pull the session information.

    The following PYTHON variables should be set:
     - `BOT_MODE` True if the script should run in 'bot' mode, meaning it is not saving to file but is instead checking for changes and keeping track of sessions in DynamoDB. If set to False, this will save all of the re:Invent sessions to a text file called 'sessions.txt'
     - `TWEET`: True if the script should be tweeting out changes. Only used if BOT_MODE is also True.

2. `single_session_topic.py` - Takes in a single Topic ID # via an environment variable. Then pulls all of the sessions in the topic.

    The following ENVRIRONMENT variables should be set:
     - `REINVENT_TOPIC_ID`: a numeric topic ID
     - `REINVENT_BOT_MODE`: True if the script should run in 'bot' mode, meaning it is not saving to file but is instead checking for changes and keeping track of sessions in DynamoDB. If set to False, this will save all of the re:Invent sessions to a text file called 'sessions.txt'
     - `REINVENT_TWEET`: True if the script should be tweeting out changes. Only used it REINVENT_BOT_MODE is also True.
     - `REINVENT_EXEC_TIMESTAMP`: A timestamp passed in and used for logging across multiple invocations of the script.

    As mentioned, the single session script can take in a single topic ID # via an environment variable. This was designed so that it could be used in a distributed fashion, via a Docker container. The folder    `topic_lister` is designed as a Lambda Function which uses the Python requests module and BS4 module to pull re:Invent session topics and IDs, and then run a task in Fargate for each topic.

## How these scripts work

For more information on the functionality, [visit the Medium article here](https://medium.com/@mda590/inside-the-aws-re-invent-session-bot-c353830e2104).