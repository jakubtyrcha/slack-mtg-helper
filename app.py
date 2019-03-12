from flask import abort, Flask, jsonify, request
from cmds import Result, handle_command
import os

app = Flask(__name__)

def is_request_valid(request):
    is_token_valid = request.form['token'] == os.environ['SLACK_VERIFICATION_TOKEN']
    is_team_id_valid = request.form['team_id'] == os.environ['SLACK_TEAM_ID']

    return is_token_valid and is_team_id_valid

@app.route('/mtg-tournament', methods=['POST'])
def new_tournament():
    print(request)
    print(request.form)
    if not is_request_valid(request):
        abort(400)

    user = request.form['user_name']
    cmd = request.form['text'][:1000]

    result = handle_command(user, cmd)
    if result:
        if isinstance(result, Result):
            return result.get_json()
        return result

    return jsonify(
        response_type='ephemeral',
        text="Failed to handle the request, try 'help'?",
    )
