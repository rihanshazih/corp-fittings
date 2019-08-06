import json
import boto3

from util import DecimalEncoder

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
structures_table = dynamodb.Table('corp-fittings-doctrines')


def handle(event, context):
    doctrine_response = structures_table.scan()
    doctrines = doctrine_response['Items']

    return {
        "statusCode": 200,
        "body": json.dumps(doctrines, cls=DecimalEncoder)
    }
