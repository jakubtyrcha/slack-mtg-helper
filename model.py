# table 'Tournament'
# id, name, date, deleted

# table 'Duels'
# id, player0, player1, score, deleted, tournament-id (secondary)

# table 'History'
# id, user, date, modification, duel_id, tournament-id (secondary)

from __future__ import print_function # Python 2/3 compatibility
import boto3
from boto3.dynamodb.conditions import Key, Attr

class Duel(object):
    def __init__(self, initial_data):
        for key in initial_data:
            setattr(self, key, initial_data[key])

        self.score = tuple(int(x) for x in self.score.split('-'))
        self.id = int(self.id)
        self.tid = int(self.tid)

class History(object):
    def __init__(self, initial_data):
        for key in initial_data:
            setattr(self, key, initial_data[key])

class Model:
    def __init__(self):
        self.dynamodb_client = boto3.client('dynamodb')
        self.dynamodb = boto3.resource('dynamodb', region_name='us-west-2', endpoint_url="http://localhost:8000")
        self.tournaments_table = None
        self.duels_table = None
        self.history_table = None
        self.counters_table = None

    def init(self):
        self.create_tables()

    def create_tables(self):
        dynamodb = self.dynamodb
        try:
            self.counters_table = dynamodb.create_table(
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

            self.counters_table.put_item(
                Item={
                    'name': 'TournamentId',
                    'ctr': 0,
                }
            )
        except self.dynamodb_client.exceptions.ResourceInUseException:
            self.counters_table = dynamodb.Table('Counters')

        try:
             self.tournaments_table = dynamodb.create_table(
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
        except self.dynamodb_client.exceptions.ResourceInUseException:
            self.tournaments_table = dynamodb.Table('Tournaments')
        try:
             self.duels_table = dynamodb.create_table(
                TableName='Duels',
                KeySchema=[
                    {
                        'AttributeName': 'tid',
                        'KeyType': 'HASH'
                    },
                    {
                        'AttributeName': 'id',
                        'KeyType': 'RANGE'
                    },
                ],
                AttributeDefinitions=[
                    {
                        'AttributeName': 'tid',
                        'AttributeType': 'N'
                    },
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
        except self.dynamodb_client.exceptions.ResourceInUseException:
            self.duels_table = dynamodb.Table("Duels")

        try:
             self.history_table = dynamodb.create_table(
                TableName='History',
                KeySchema=[
                    {
                        'AttributeName': 'tid',
                        'KeyType': 'HASH'
                    },
                    {
                        'AttributeName': 'id',
                        'KeyType': 'RANGE'
                    },
                ],
                AttributeDefinitions=[
                    {
                        'AttributeName': 'tid',
                        'AttributeType': 'N'
                    },
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
        except self.dynamodb_client.exceptions.ResourceInUseException:
            self.history_table = dynamodb.Table('History')

    def last_tournament_id(self):
        list = self.get_tournaments()
        if len(list) == 0:
            return -1
        return int(max(list, key=lambda x: x['date'])['id'])

    def get_tournaments(self):
        result = self.tournaments_table.scan()
        return sorted(result['Items'], key=lambda x: x['date'])

    def add_tournament(self, name, user, date):
        response = self.counters_table.update_item(
            Key={
                'name': 'TournamentId'
            },
            UpdateExpression="set ctr = ctr+:val",
            ExpressionAttributeValues={
                ':val': 1
            },
            ReturnValues="UPDATED_NEW"
        )
        tid = int(response['Attributes']['ctr'])

        self.tournaments_table.put_item(
               Item={
                   'id': tid,
                   'name': name,
                   'date': date,
                   'deleted' : False,
                   'did' : 0,
                   'hid' : 0
                }
            )

    def delete_tournament(self, tid, user, date):
        self.tournaments_table.update_item(
            Key={
                'id': tid
            },
            UpdateExpression="set deleted=:b",
            ExpressionAttributeValues={
                ':b': True,
            }
        )

    def add_duel(self, tid, player0, player1, score, user, date):
        response = self.tournaments_table.update_item(
            Key={
                'id': tid
            },
            UpdateExpression="set did = did+:val, hid = hid+:val",
            ExpressionAttributeValues={
                ':val': 1
            },
            ReturnValues="UPDATED_NEW"
        )
        id = int(response['Attributes']['did'])
        hid = int(response['Attributes']['hid'])

        result = self.duels_table.put_item(
            Item={
                'id': id,
                'tid' : tid,
                'player0' : player0,
                'player1' : player1,
                'score' : score,
                'deleted' : False
            }
        )

        self.history_table.put_item(
            Item={
                'id' : hid,
                'user' : user,
                'date' : date,
                'mod' : "+",
                'did' : id,
                'tid' : tid
            }
        )

    def delete_duel(self, tid, id, user, date):
        response = self.tournaments_table.update_item(
            Key={
                'id': tid
            },
            UpdateExpression="set hid = hid+:val",
            ExpressionAttributeValues={
                ':val': 1
            },
            ReturnValues="UPDATED_NEW"
        )
        hid = int(response['Attributes']['hid'])

        self.duels_table.update_item(
            Key={
                'id': id,
                'tid': tid
            },
            UpdateExpression="set deleted=:b",
            ExpressionAttributeValues={
                ':b': True,
            }
        )

        self.history_table.put_item(
            Item={
                'id': hid,
                'user': user,
                'date': date,
                'mod': "-",
                'did': id,
                'tid': tid
            }
        )

    def get_duels(self, tid):
        response = self.duels_table.query(
            KeyConditionExpression=Key('tid').eq(tid),
            FilterExpression=Attr('deleted').eq(False)
        )
        return [Duel(x) for x in response['Items']]

    def get_duels_including_deleted(self, tid):
        response = self.duels_table.query(
            KeyConditionExpression=Key('tid').eq(tid)
        )
        return [Duel(x) for x in response['Items']]

    def get_history(self, tid):
        response = self.history_table.query(
            KeyConditionExpression=Key('tid').eq(tid)
        )
        print(response['Items'])
        return [History(x) for x in response['Items']]

    def destory_tables(self):
        if self.counters_table:
            self.counters_table.delete()
        if self.history_table:
            self.history_table.delete()
        if self.tournaments_table:
            self.tournaments_table.delete()
        if self.duels_table:
            self.duels_table.delete()

if __name__ == "__main__":
    model = Model()

    try:
        model.create_tables()

        model.add_tournament('Draft 0', '@joe', '2019-08-11')
        model.delete_tournament(1, '@joe', '2019')
        model.add_tournament('Draft 1', '@joe', '2019-08-22 11:12:11')

        model.add_duel(1, '@joe', '@jakub', '2-1', '@joe', '2019-08-22 11:12:11')
        model.add_duel(2, '@joe', '@jakub', '2-1', '@joe', '2019-08-22 11:12:11')
        model.add_duel(2, '@joe', '@jakub', '2-1', '@joe', '2019-08-22 11:12:11')
        model.add_duel(2, '@joe', '@jakub', '3-1', '@joe', '2019-08-22 11:12:11')
        model.add_duel(2, '@joe', '@jakub', '4-1', '@joe', '2019-08-22 11:12:11')
        model.delete_duel(2, 2, '@joe', '2019-08-22 11:12:11')

        print(len(model.get_duels(1)))

        print(len(model.get_history(1)))

        print(model.get_tournaments())
        print(model.last_tournament_id())

        model.destory_tables()
    except:
        model.destory_tables()
        raise






