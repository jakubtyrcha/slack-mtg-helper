from flask import abort, Flask, jsonify, request
from cmds import Result, handle_command, on_create_tournament, on_add_duel, on_list_duels
import os
import json
from dialog import CreateTournamentDialog, AddDuelDialog

app = Flask(__name__)

from slackclient import SlackClient

slack_token = os.environ["SLACK_VERIFICATION_TOKEN"]
slack_client = SlackClient("xoxb-571211179077-573885904464-TsLsBJyywxfhaLg3qFQrsRKg")

def is_request_valid(request):
    is_token_valid = request.form['token'] == os.environ['SLACK_VERIFICATION_TOKEN']
    #is_team_id_valid = request.form['team_id'] == os.environ['SLACK_TEAM_ID']

    return is_token_valid #and is_team_id_valid

@app.route('/mtg-util', methods=['POST'])
def handle_util():
    print(request.form)
    if not is_request_valid(request):
        abort(400)

    user = request.form['user_name']
    cmd = request.form['text'][:1000]

    result = handle_command(user, cmd)
    if result:
        if isinstance(result, Result):
            if result.text or result.blocks:
                if result.blocks:
                    return jsonify(response_type='ephemeral', text=result.text, blocks = result.blocks)
                return jsonify(response_type='ephemeral', text=result.text)
            return ('', 200)

    return jsonify(
        response_type='ephemeral',
        text="Failed to handle the request, try 'help'?",
    )

@app.route('/mtg-util-dialog', methods=['POST'])
def handle_dialog():
    message_action = json.loads(request.form["payload"])
    if not message_action['token'] == os.environ['SLACK_VERIFICATION_TOKEN']:
        abort(400)

    print(message_action)

    def get_username(message_action):
        if "user" in message_action["user"]:
            return message_action["user"]["user"]
        elif "username" in message_action["user"]:
            return message_action["user"]["username"]

    user_id = message_action["user"]["id"]
    user_name = get_username(message_action)

    CREATE_TOURNAMENT_CALLBACK = "create_tournament"
    ADD_DUEL_CALLBACK = "add_duel"

    if message_action["type"] == "block_actions":

        for action in message_action["actions"]:

            if action["type"] == "static_select" or action["type"] == "overflow":
                print(action["selected_option"]["value"])

                cmd_args = action["selected_option"]["value"].split(";")

                if cmd_args[0] == "add_duel":
                    slack_client.api_call(
                        "dialog.open",
                        trigger_id=message_action["trigger_id"],
                        dialog=AddDuelDialog(slack_client, "Add duel",
                                                      ADD_DUEL_CALLBACK, cmd_args[1]).construct()
                    )
                if cmd_args[0] == 'list_duels':
                    result = on_list_duels(int(cmd_args[1]))

                    r = slack_client.api_call(
                        "chat.postEphemeral",
                        channel=message_action["channel"]["id"],
                        blocks=result.blocks,
                        text=result.text,
                        user=user_id
                    )
                    print(r)

            if action["type"] == "button":
                if action["value"] == 'add_tournament':
                    r = slack_client.api_call(
                        "dialog.open",
                        trigger_id=message_action["trigger_id"],
                        dialog=CreateTournamentDialog(slack_client, "Create tournament", CREATE_TOURNAMENT_CALLBACK).construct()
                    )
                    print(r)
    elif message_action["type"] == "dialog_submission":
        if message_action["callback_id"] == CREATE_TOURNAMENT_CALLBACK:
            name = message_action["submission"]["name"]
            on_create_tournament(user_name, name)
        elif message_action["callback_id"] == ADD_DUEL_CALLBACK:
            print(message_action["submission"])
            player0 = message_action["submission"]["player_0"]
            player1 = message_action["submission"]["player_1"]
            score0 = int(message_action["submission"]["score_0"])
            score1 = int(message_action["submission"]["score_1"])
            tid = int(message_action["state"])
            on_add_duel(tid, user_name, player0, player1, (score0, score1))

    return ('', 200)
