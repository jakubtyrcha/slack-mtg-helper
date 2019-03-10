# table 'Tournament'
# id, name, date, deleted

# table 'Duels'
# id, player0, player1, score, deleted, tournament-id (secondary)

# table 'History'
# id, user, date, modification, duel_id, tournament-id (secondary)

from __future__ import print_function # Python 2/3 compatibility
import boto3

dynamodb_client = boto3.client('dynamodb')
dynamodb = boto3.resource('dynamodb', region_name='us-west-2', endpoint_url="http://localhost:8000")

def init(dynamodb):
    try:
        counters_table = dynamodb.create_table(
            TableName='Counters',
            KeySchema=[
                {
                    'AttributeName': 'name',
                    'KeyType': 'HASH'
                },
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'name',
                    'AttributeType': 'S'
                },

            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 10,
                'WriteCapacityUnits': 10
            }
        )

        counters_table.put_item(
            Item={
                'name': 'TableId',
                'ctr': 0,
            }
        )
        counters_table.put_item(
            Item={
                'name': 'DuelId',
                'ctr': 0,
            }
        )
        counters_table.put_item(
            Item={
                'name': 'HistoryId',
                'ctr': 0,
            }
        )
    except dynamodb_client.exceptions.ResourceInUseException:
        pass

    try:
         dynamodb.create_table(
            TableName='Tournaments',
            KeySchema=[
                {
                    'AttributeName': 'id',
                    'KeyType': 'HASH'
                },
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'id',
                    'AttributeType': 'N'
                },

            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 10,
                'WriteCapacityUnits': 10
            }
        )
    except dynamodb_client.exceptions.ResourceInUseException:
        pass
    try:
         dynamodb.create_table(
            TableName='Duels',
            KeySchema=[
                {
                    'AttributeName': 'id',
                    'KeyType': 'HASH'
                },
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'id',
                    'AttributeType': 'N'
                },

            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 10,
                'WriteCapacityUnits': 10
            }
        )
    except dynamodb_client.exceptions.ResourceInUseException:
        pass

    try:
         dynamodb.create_table(
            TableName='History',
            KeySchema=[
                {
                    'AttributeName': 'id',
                    'KeyType': 'HASH'
                },
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'id',
                    'AttributeType': 'N'
                },

            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 10,
                'WriteCapacityUnits': 10
            }
        )
    except dynamodb_client.exceptions.ResourceInUseException:
        pass



tournaments_table = dynamodb.Table('Tournaments')
duels_table = dynamodb.Table('Duels')
history_table = dynamodb.Table('History')
counters_table = dynamodb.Table('Counters')

def gen_id(name):
    response = counters_table.update_item(
        Key={
            'name': name
        },
        UpdateExpression="set ctr = ctr+:val",
        ExpressionAttributeValues={
            ':val': 1
        },
        ReturnValues="UPDATED_NEW"
    )
    return int(response['Attributes']['ctr'])

def add_tournament(id, name, date):
    tournaments_table.put_item(
           Item={
               'id': id,
               'name': name,
               'date': date,
               'deleted' : False
            }
        )

def delete_tournament(id):
    tournaments_table.update_item(
        Key={
            'id': id
        },
        UpdateExpression="set deleted=:b",
        ExpressionAttributeValues={
            ':b': True,
        }
    )

def add_duel(id, user, date, tid, player0, player1, score):
    hid = gen_id('HistoryId')

    duels_table.put_item(
        Item={
            'id': id,
            'user' : user,
            'tid' : tid,
            'player0' : player0,
            'player1' : player1,
            'score' : score,
            'deleted' : False
        }
    )

    history_table.put_item(
        Item={
            'id' : hid,
            'user' : user,
            'date' : date,
            'mod' : "+",
            'did' : id,
            'tid' : tid
        }
    )

def delete_duel(id, user, date, tid):
    hid = gen_id('HistoryId')

    duels_table.update_item(
        Key={
            'id': id
        },
        UpdateExpression="set deleted=:b",
        ExpressionAttributeValues={
            ':b': True,
        }
    )

    history_table.put_item(
        Item={
            'id': hid,
            'user': user,
            'date': date,
            'mod': "-",
            'did': id,
            'tid': tid
        }
    )

if __name__ == "__main__":
    init(dynamodb)

    add_tournament(0, 'Draft 0', '2019-08-11')
    delete_tournament(0)
    add_tournament(1, 'Draft 1', '2019-08-22 11:12:11')

    did = gen_id('DuelId')
    add_duel(did, '@joe', '2019-08-22 11:12:11', 1, '@joe', '@jakub', '2-1')
    add_duel(gen_id('DuelId'), '@joe', '2019-08-22 11:12:11', 1, '@joe', '@jakub', '2-1')
    delete_duel(did, '@joe', '2019-08-22 11:12:11', 1)

