import json
import boto3
from boto3.dynamodb.conditions import Key
import urllib.parse

from util import DecimalEncoder

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('corp-fittings-fittings')


def handle(event, context):
    fitting_name = urllib.parse.unquote(event['pathParameters']['name'])
    response = table.query(
        KeyConditionExpression=Key('fitting_name').eq(fitting_name)
    )

    if response['Count'] == 0:
        return {
            "statusCode": 404
        }

    body = response['Items'][0]
    return {
        "statusCode": 200,
        "body": json.dumps(body, cls=DecimalEncoder)
    }
