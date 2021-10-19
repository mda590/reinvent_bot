# AWS re:Invent Session Downloader & Twitter Bot (Updated for 2021!)

## This repo contains code which provides 2 pieces of functionality

1. **Download re:Invent sessions to a text file** - While the re:Invent catalog website is brand new for 2021, it still has some pain points. With 100's of sessions offered, it's difficult to use the session catalog and feel comfortable that you've seen everything you may want to attend. This script will allow you to download all of the re:Invent sessions from the catalog to a text file which you can then parse and manipulate in any way you wish. It also includes a column for whether you've starred the session or not.

2. **Twitter Bot** - This script stores every re:Invent session in a database and keeps track of changes to sessions by adding new records to the database with new versions. In the event that a new session is detected or there is a change to an existing session, this script will use the Twitter API to send a Tweet from the @reinvent_bot account.

The above 2 pieces of functionality work independently of each other and can be toggled on/off by changing a few variables.

## How to generate a list of sessions

1. Install the required Python packages listed in `requirements.txt`.
2. Copy the `config.example.py` file to `config.py` and update the values for `AWS_EVENTS_USERNAME` and `AWS_EVENTS_PASSWORD` to match your portal login.
3. Run the `reinvent_graphql.py` as it is (ensuring that `BOT_MODE` and `TWEET` are both False).
4. Sessions will be downloaded and then saved to a file called `sessions.csv`.

## The file and inputs

`reinvent_graphql.py` - Grabs the list of sessions 100 at a time from the new GraphQL endpoint. Loops through each session and saves to a file and/or tweets out updates.

The following PYTHON or environment variables should be set:

- `BOT_MODE` True if the script should run in 'bot' mode, meaning it is not saving to file but is instead checking for changes and keeping track of sessions in DynamoDB. If set to False, this will save all of the re:Invent sessions to a text file called 'sessions.txt'
- `TWEET`: True if the script should be tweeting out changes. Only used if BOT_MODE is also True.

## How this script works

With the launch of the new re:Invent catalog in 2021, there are some exciting changes that make this process easier!

- Authentication to the AWS Events site (& therefore, the re:Invent Portal) are handled via AWS Cognito.
- The Session data is stored in a GraphQL database and accessible via a simple API call.
- The GraphQL data is protected by credentials provided when authenticating with Cognito, available via each user's specific login to the portal.
- Once the GraphQL token is retrieved from Cognito, the sessions list is pulled via a few simple API calls
