import json
import boto3
from decimal import Decimal

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
structures_table = dynamodb.Table('corp-fittings-fittings')


def handle(event, context):
    print(event['body'])
    fitting = json.loads(event['body'])

    structures_table.put_item(Item=json.loads(json.dumps(fitting), parse_float=Decimal))

    return {
        "statusCode": 201
    }
