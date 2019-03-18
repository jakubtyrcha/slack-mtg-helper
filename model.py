from __future__ import print_function # Python 2/3 compatibility
import boto3
from boto3.dynamodb.conditions import Key, Attr

class Model:
    def __init__(self):
        self.dynamodb_client = boto3.client('dynamodb')
        self.dynamodb = boto3.resource('dynamodb', region_name='us-west-2', endpoint_url="http://localhost:8000")
        self.tournaments_table = None
        self.duels_table = None
        self.id_table = None

    def init(self):
        self.create_tables()

    def destory_tables(self):
        if self.id_table:
            self.id_table.delete()
        if self.tournaments_table:
            self.tournaments_table.delete()
        if self.duels_table:
            self.duels_table.delete()

    def create_tables(self):
        self.create_id_table()
        self.create_tournaments_table()
        self.create_duels_table()

    def create_id_table(self):
        dynamodb = self.dynamodb
        try:
            self.id_table = dynamodb.create_table(
                TableName='NextId',
                KeySchema=[
                    {
                        'AttributeName': 'id',
                        'KeyType': 'HASH'
                    },
                ],
                AttributeDefinitions=[
                    {
                        'AttributeName': 'id',
                        'AttributeType': 'S'
                    },
                ],
                ProvisionedThroughput={
                    'ReadCapacityUnits': 10,
                    'WriteCapacityUnits': 10
                }
            )
        except self.dynamodb_client.exceptions.ResourceInUseException:
            self.id_table = dynamodb.Table('NextId')

    def create_tournaments_table(self):
        dynamodb = self.dynamodb
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

    def create_duels_table(self):
        dynamodb = self.dynamodb
        try:
            self.duels_table = dynamodb.create_table(
                TableName='Duels',
                KeySchema=[
                    {
                        'AttributeName': 'tournament_id',
                        'KeyType': 'HASH'
                    },
                    {
                        'AttributeName': 'id',
                        'KeyType': 'Range'
                    },
                ],
                AttributeDefinitions=[
                    {
                        'AttributeName': 'tournament_id',
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
            self.duels_table = dynamodb.Table('Duels')

    def allocate_new_tournament_id(self):
        response = self.id_table.update_item(
            Key={
                'id': "global_tournament_id"
            },
            UpdateExpression="add global_tournament_id :val",
            ExpressionAttributeValues={
                ':val': 1
            },
            ReturnValues="UPDATED_NEW"
        )
        return int(response['Attributes']['global_tournament_id'])

    def create_tournament_row(self, tournament_id, channel_id, name, date):
        response = self.tournaments_table.put_item(
            Item={
                'id': tournament_id,
                'channel_id': channel_id,
                'name': name,
                'deleted' : False,
                'closed' : False,
                'date' : date
            }
        )

    def register_tournament_thread_ts(self, tournament_id, thread_ts):
        response = self.tournaments_table.update_item(
            Key={
                'id': tournament_id
            },
            UpdateExpression="set thread_ts = :val",
            ExpressionAttributeValues={
                ':val': thread_ts
            }
        )

    def register_duel_message_ts(self, tournament_id, duel_id, ts):
        response = self.duels_table.update_item(
            Key={
                'id': duel_id,
                'tournament_id' : tournament_id
            },
            UpdateExpression="set message_ts = :val",
            ExpressionAttributeValues={
                ':val': ts
            }
        )

    def settle_winner(self, tournament_id, player):
        try:
            response = self.tournaments_table.update_item(
                Key={
                    'id': tournament_id
                },
                UpdateExpression="set winner = :val, closed = :c",
                ConditionExpression="closed = :cv",
                ExpressionAttributeValues={
                    ':val': player,
                    ':c': True,
                    ':cv' : False
                }
            )

            return True
        except self.dynamodb_client.exceptions.ConditionalCheckFailedException:
            return False

    def query_tournament(self, tournament_id):
        resp = self.tournaments_table.query(
            KeyConditionExpression=Key('id').eq(tournament_id)
        )
        return resp['Items'][0]

    def query_tournament_thread_ts(self, tournament_id):
        resp = self.tournaments_table.query(
            KeyConditionExpression=Key('id').eq(tournament_id)
        )
        return resp['Items'][0]['thread_ts']

    def create_duel_row(self, channel_id, user_id, tournament_id, duel_score, user_name, date):
        response = self.tournaments_table.update_item(
            Key={
                'id': tournament_id
            },
            UpdateExpression="add next_duel_id :val",
            ExpressionAttributeValues={
                ':val': 1
            },
            ReturnValues="UPDATED_NEW"
        )
        duel_id = int(response['Attributes']['next_duel_id'])

        response = self.duels_table.put_item(
            Item={
                'id': duel_id,
                'tournament_id': tournament_id,
                'p0': duel_score[0][0],
                'p1': duel_score[1][0],
                'score0': duel_score[0][1],
                'score1': duel_score[1][1],
                'deleted': False,
                'added_by' : user_name,
                'added_date' : date
            }
        )

        return duel_id

    def delete_duel(self, tournament_id, duel_id, user_name, date):
        response = self.duels_table.update_item(
            Key={
                'id': duel_id,
                'tournament_id' : tournament_id
            },
            UpdateExpression="set deleted = :val, deleted_by = :a, deleted_date = :d",
            ExpressionAttributeValues={
                ':val': True,
                ':a' : user_name,
                ':d' : date
            },
            ReturnValues="UPDATED_NEW"
        )

    def query_duel(self, tournament_id, duel_id):
        resp = self.duels_table.query(
            KeyConditionExpression=Key('id').eq(duel_id) & Key('tournament_id').eq(tournament_id)
        )
        return resp['Items'][0]

    def remove_tournament(self, tournament_id):
        self.tournaments_table.delete_item(
            Key={
                'id': tournament_id
            }
        )

    def delete_tournament(self, channel_id, tournament_id):
        response = self.tournaments_table.update_item(
            Key={
                'id': tournament_id
            },
            UpdateExpression="set deleted = :val",
            ExpressionAttributeValues={
                ':val': True
            },
            ReturnValues="UPDATED_NEW"
        )

    def query_duels(self, tournament_id):
        resp = self.duels_table.query(
            KeyConditionExpression=Key('tournament_id').eq(tournament_id),
            FilterExpression=Attr('deleted').eq(False)
        )
        return resp['Items']

if __name__ == "__main__":
    model = Model()

    try:
        model.create_tables()
        model.destory_tables()
        model.create_tables()

    except:
        model.destory_tables()
        raise