from bs4 import BeautifulSoup
from datetime import datetime
from time import sleep

import boto3
import requests

ecs_client = boto3.client('ecs')

def submit_to_fargate(topic_id, execution_timestamp):
    response = ecs_client.run_task(
        cluster='fargate',
        taskDefinition='arn:aws:ecs:us-east-2:506666621600:task-definition/reinvent_bot_2018:1',
        overrides={
            'containerOverrides': [
                {
                    'name': 'reinvent_bot',
                    'environment': [
                        {
                            'name': 'REINVENT_TOPIC_ID',
                            'value': topic_id
                        },
                        {
                            'name': 'REINVENT_EXEC_TIMESTAMP',
                            'value': execution_timestamp
                        },
                        {
                            'name': 'REINVENT_TWEET',
                            'value': 'True'
                        },					
                    ]
                },
            ]
        },
        launchType='FARGATE',
        networkConfiguration={
            'awsvpcConfiguration': {
                'subnets': [
                    'subnet-41a2ab39',
                ],
                'securityGroups': [
                    'sg-682ede01',
                ],
                'assignPublicIp': 'ENABLED'
            }
        }
    )

    return response['tasks'][0]['taskArn']

def lambda_handler(event, context):
    execution_timestamp = str(datetime.now())
    r = requests.get("https://www.portal.reinvent.awsevents.com/connect/search.ww")

    soup = BeautifulSoup(r.text, "html.parser")

    topic_ids = []

    topics = soup.find("div", id="profileItem_19577_tr")
    topics = topics.find("div", class_="formContent")
    topics = topics.find_all("input")
    for t in topics:
        topic_id = t['value']
        print("Submitting Task to Fargate For Topic ID: {}".format(topic_id))
        topic_ids.append(topic_id)
        task_arn = submit_to_fargate(topic_id, execution_timestamp)
        print("Topic Task Arn: {}".format(task_arn))
        sleep(.5)

if __name__ == '__main__':
    lambda_handler("", "")
