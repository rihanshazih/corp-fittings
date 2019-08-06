import json

import boto3
from boto3.dynamodb.conditions import Key
from requests_futures.sessions import FuturesSession

from util import DecimalEncoder

session = FuturesSession()

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
fittings_table = dynamodb.Table('corp-fittings-fittings')
doctrines_table = dynamodb.Table('corp-fittings-doctrines')


def get_fitting_items(fitting_name, multiplier):
    db_response = fittings_table.query(
        KeyConditionExpression=Key('fitting_name').eq(fitting_name)
    )
    if db_response['Count'] == 0:
        return []
    fitting = db_response['Items'][0]

    fitting_items = []
    if 'ammo' in fitting:
        fitting_items.extend(fitting['ammo'])
    if 'drones' in fitting:
        fitting_items.extend(fitting['drones'])
    if 'high' in fitting:
        fitting_items.extend(fitting['high'])
    if 'med' in fitting:
        fitting_items.extend(fitting['med'])
    if 'low' in fitting:
        fitting_items.extend(fitting['low'])
    if 'rigs' in fitting:
        fitting_items.extend(fitting['rigs'])
    fitting_items.append({
        'name': fitting['hull'],
        'quantity': 1
    })

    for fitting_item in fitting_items:
        fitting_item['quantity'] = int(multiplier) * int(fitting_item['quantity'])

    return fitting_items


def make_chunks(l, chunk_length):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), chunk_length):
        yield l[i:i + chunk_length]


def get_inventory_types(names):
    result = {}
    if len(names) > 0:
        for chunk in make_chunks(names, 500):
            # we are not doing any status or contains checks here, because we want the api to fail if
            # esi doesn't return the required data
            response = session.post('https://esi.evetech.net/v1/universe/ids/',
                                    headers={'User-Agent': 'Rihan Shazih - Corp Fittings'},
                                    data=json.dumps(chunk)).result()
            body = response.json()
            for inventory_type in body['inventory_types']:
                result[inventory_type['name']] = inventory_type['id']
    return result


def handle(event, context):

    grouped_by_structure = {}
    names = []

    print('Loading doctrines')
    db_doctrines = doctrines_table.scan()
    if db_doctrines['Count'] > 0:
        for doctrine in db_doctrines['Items']:
            if 'structure_ids' not in doctrine or 'fittings' not in doctrine:
                print('Skipping invalid doctrine %s' % doctrine)
                continue
            structure_ids = doctrine['structure_ids']
            doctrine_items = []
            print('Evaluating fittings for doctrine %s' % doctrine['doctrine_name'])
            for doctrine_fitting in doctrine['fittings']:
                if 'fitting_name' not in doctrine_fitting or 'quantity' not in doctrine_fitting:
                    print('Skipping invalid fitting %s' % doctrine_fitting)
                    continue
                print('Collecting items for fitting %s' % doctrine_fitting['fitting_name'])
                print(doctrine_fitting)
                doctrine_items.extend(get_fitting_items(doctrine_fitting['fitting_name'], doctrine_fitting['quantity']))

            print('Grouping doctrine items by structures')
            for structure_id in structure_ids:
                structure_id = int(structure_id)
                if structure_id not in grouped_by_structure:
                    grouped_by_structure[structure_id] = []
                grouped_by_structure[structure_id].extend(doctrine_items)

            print('Collecting item names')
            for item in doctrine_items:
                names.append(item['name'])

    names = list(set(names))
    print('Loading %d inventory types' % len(names))
    inventory_types = get_inventory_types(names)

    print('Building response')
    result = []
    for structure_id, doctrine_items in grouped_by_structure.items():
        grouped_volumes = {}
        for item in doctrine_items:
            type_id = inventory_types[item['name']]
            quantity = item['quantity']
            if type_id not in grouped_volumes:
                grouped_volumes[type_id] = 0
            grouped_volumes[type_id] += quantity

        for type_id, volume in grouped_volumes.items():
            result.append({
                'typeId': type_id,
                'threshold': volume,
                'orderType': 'sell',
                'comparator': 'lt',
                'structureId': structure_id
            })

    return {
        "statusCode": 200,
        "body": json.dumps(result, cls=DecimalEncoder)
    }
