import json
import boto3
from decimal import Decimal

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('corp-fittings-doctrines')


def handle(event, context):
    print(event['body'])
    doctrine = json.loads(event['body'])

    table.put_item(Item=json.loads(json.dumps(doctrine), parse_float=Decimal))

    return {
        "statusCode": 201
    }
