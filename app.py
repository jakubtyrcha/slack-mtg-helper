from flask import abort, Flask, jsonify, request
import os, json, datetime
from dialogs import NewTournamentDialog, AddDuelDialog, BlocksBuilder
import dateutil.parser

def date_token_now():
    return datetime.datetime.now().isoformat()

def pretty_date(d):
    return dateutil.parser.parse(d).strftime("%d %b %Y %X")

app = Flask(__name__)

from slackclient import SlackClient

slack_token = os.environ["SLACK_VERIFICATION_TOKEN"]
slack_client = SlackClient(os.environ["SLACK_BOT_TOKEN"])

LEGACY_SLACK_CLIENT_NOT_SUPPORTED = ""

LOG_SERVER_RESPONSES = False

from model import Model
from itertools import product, groupby

model = Model()
model.init()

def make_callback_value(*args):
    return ";".join([str(a) for a in args])

def parse_callback_value(value):
    return value.split(";")

def create_tournament_thread(tournament_id, channel_id, user_id, user_name, tournament_name, date):
    blocks = BlocksBuilder().section("Tournament *{}*".format(tournament_name))\
        .button("Add duel", make_callback_value("add_duel_dialog", tournament_id)) \
        .button("Current standing", make_callback_value("tournament_report", tournament_id)) \
        .button("Close tournament", make_callback_value("close_tournanent", tournament_id)) \
        .button("Delete tournament", make_callback_value("delete_tournament", tournament_id)) \
            .with_confirm_simple("Are you sure?", "Delete tournament", "Cancel") \
        .context("created {} by {}".format(pretty_date(date), user_name))

    resp = slack_client.api_call(
        "chat.postMessage",
        channel=channel_id,
        user=user_id,
        blocks=blocks.construct(),
        text=LEGACY_SLACK_CLIENT_NOT_SUPPORTED
    )

    if LOG_SERVER_RESPONSES:
        print(resp)

    if resp["ok"]:
        model.register_tournament_thread_ts(tournament_id, resp["ts"])
    else:
        # error message
        model.remove_tournament(tournament_id)

def publish_duel_result(channel_id, thread_ts, tournament_id, duel_id, duel_score, user_name, date):
    p0, score0 = duel_score[0]
    p1, score1 = duel_score[1]
    blocks = BlocksBuilder().section("_{}_ {}-{} _{}_".format(p0, score0, score1, p1))\
        .button("Delete", make_callback_value("delete_duel", tournament_id, duel_id)) \
            .with_confirm_simple("Are you sure?", "Delete duel", "Cancel") \
        .context("added {} by {}".format(pretty_date(date), user_name))

    resp = slack_client.api_call(
        "chat.postMessage",
        channel=channel_id,
        thread_ts=thread_ts,
        blocks=blocks.construct(),
        text=LEGACY_SLACK_CLIENT_NOT_SUPPORTED
    )

    if LOG_SERVER_RESPONSES:
        print(resp)

    if resp['ok']:
        model.register_duel_message_ts(tournament_id, duel_id, resp['ts'])

def is_request_valid(request):
    is_token_valid = request.form['token'] == os.environ['SLACK_VERIFICATION_TOKEN']
    return is_token_valid

def create_new_tournament_dialog(trigger_id):
    slack_client.api_call(
        "dialog.open",
        trigger_id=trigger_id,
        dialog=NewTournamentDialog(slack_client, "New tournament wizard",
                             make_callback_value("new_tournament_submitted")).construct()
    )

def create_add_duel_dialog(trigger_id, tournament_id):
    slack_client.api_call(
        "dialog.open",
        trigger_id=trigger_id,
        dialog=AddDuelDialog(slack_client, "Add duel wizard",
                                   make_callback_value("new_duel_submitted"), str(tournament_id)).construct()
    )

def create_new_tournament(channel_id, user_id, user_name, name, date):
    tournament_id = model.allocate_new_tournament_id()
    model.create_tournament_row(tournament_id, channel_id, name, date)
    thread_id = create_tournament_thread(tournament_id, channel_id, user_id, user_name, name, date)
    if thread_id:
        model.register_tournament_thread_ts(tournament_id, thread_id)

def add_new_duel(channel_id, user_id, tournament_id, duel_score, user_name):
    date = date_token_now()
    duel_id = model.create_duel_row(channel_id, user_id, tournament_id, duel_score, user_name, date)
    publish_duel_result(channel_id, model.query_tournament_thread_ts(tournament_id), tournament_id, duel_id, duel_score, user_name, date)

def delete_duel_and_update_message(channel_id, tournament_id, duel_id, message_ts, user_name):
    q = model.query_duel(tournament_id, duel_id)
    duel_score = ((q['p0'], int(q['score0'])), (q['p1'], int(q['score1'])))
    p0, score0 = duel_score[0]
    p1, score1 = duel_score[1]
    date = date_token_now()
    model.delete_duel(tournament_id, duel_id, user_name, date)
    blocks = BlocksBuilder().section("~_{}_ {}-{} _{}_~".format(p0, score0, score1, p1)) \
        .context("added {} by {}".format(pretty_date(q['added_date']), q['added_by']))\
        .context("deleted {} by {}".format(pretty_date(date), user_name))

    resp = slack_client.api_call(
        "chat.update",
        channel=channel_id,
        ts=message_ts,
        blocks=blocks.construct(),
        text=LEGACY_SLACK_CLIENT_NOT_SUPPORTED
    )

    if LOG_SERVER_RESPONSES:
        print(resp)

def delete_tournament_and_remove_thread(channel_id, tournament_id):
    model.delete_tournament(channel_id, tournament_id)

    slack_client.api_call(
        "chat.delete",
        channel=channel_id,
        ts=model.query_tournament_thread_ts(tournament_id)
    )

def get_current_ranking(duels):
    players = sorted(list(set([x['p0'] for x in duels]) | set([x['p1'] for x in duels])))
    user_index = dict([(u, i) for i, u in enumerate(players)])
    matrix = [[(0, 0) for _ in players] for _ in players]

    for r in duels:
        ai = user_index[r['p0']]
        bi = user_index[r['p1']]
        wa, g = matrix[ai][bi]
        wb, _ = matrix[bi][ai]
        s0 = int(r['score0'])
        s1 = int(r['score1'])
        g += s0 + s1
        matrix[ai][bi] = (wa + s0, g)
        matrix[bi][ai] = (wb + s1, g)

    missing_duels = []
    points = dict([(p, 0) for p in players])

    for i, j in product(range(len(matrix)), repeat=2):
        if i >= j:
            continue
        if sum(matrix[i][j]) < 3 or matrix[i][j][0] == matrix[i][j][1]:
            missing_duels.append((players[i], players[j]))
        else:
            if matrix[i][j][0] > matrix[i][j][1]:
                points[players[i]] += 1
            else:
                points[players[j]] += 1

    ranking = sorted(list(points.items()), key=lambda x: -x[1])

    place = 1
    rank = []
    for k, g in groupby(ranking, key=lambda x:x[1]):
        rank.append((place, list(g)))
        place += len(rank[-1][1])

    return players, missing_duels, points, ranking, rank

def prepare_tournament_report(channel_id, tournament_id, user_id):
    duels = model.query_duels(tournament_id)
    players, missing_duels, points, ranking, rank = get_current_ranking(duels)

    blocks = BlocksBuilder().section("Current tournament standing:")

    for r in rank:
        blocks = blocks.section("{}. {}".format(r[0], ", ".join([x[0] for x in r[1]])))
    blocks.context("pairs with draws or not enough games: " + ', '.join(["({}, {})".format(d[0], d[1]) for d in missing_duels]))

    resp = slack_client.api_call(
        "chat.postEphemeral",
        channel=channel_id,
        blocks=blocks.construct(),
        text=LEGACY_SLACK_CLIENT_NOT_SUPPORTED,
        user=user_id
    )

    if LOG_SERVER_RESPONSES:
        print(resp)

def try_close_tournament(channel_id, tournament_id, user_id, user_name):
    duels = model.query_duels(tournament_id)
    players, missing_duels, points, ranking, rank = get_current_ranking(duels)

    def send_rejection_reason(text):
        resp = slack_client.api_call(
            "chat.postEphemeral",
            channel=channel_id,
            text=text,
            user=user_id
        )

        if LOG_SERVER_RESPONSES:
            print(resp)

    if len(players) < 2:
        send_rejection_reason("Can't close the tournament, not enough players to close the tournament")
        return

    if len(missing_duels) > 0:
        send_rejection_reason("Can't close the tournament, some duels are not settled")
        return

    if len(rank[0][1]) > 1:
        send_rejection_reason("Can't close the tournament, no clear winner")
        return

    winner = ranking[0][0]
    if not model.settle_winner(tournament_id, winner):
        send_rejection_reason("Can't close the tournament multiple time")
        return

    date = date_token_now()
    tournament_name = model.query_tournament(tournament_id)['name']
    blocks = BlocksBuilder().section("*{}* winner is :tada: *{}* :tada:".format(tournament_name, winner))\
        .context("closed on {} by {}".format(pretty_date(date), user_name))

    resp = slack_client.api_call(
        "chat.postMessage",
        channel=channel_id,
        blocks=blocks.construct(),
        text=LEGACY_SLACK_CLIENT_NOT_SUPPORTED
    )

    if LOG_SERVER_RESPONSES:
        print(resp)

    print(model.query_tournament(tournament_id))

@app.route('/mtg-util', methods=['POST'])
def handle_util():
    print(request.form)
    if not is_request_valid(request):
        abort(400)

    cmd = request.form['text']

    blocks = BlocksBuilder().button("Create new tournament", make_callback_value("new_tournament_dialog"))

    return jsonify(response_type='ephemeral', blocks=blocks.construct(), text=LEGACY_SLACK_CLIENT_NOT_SUPPORTED)

    return ('', 200)

@app.route('/mtg-util-dialog', methods=['POST'])
def handle_dialog():
    message_action = json.loads(request.form["payload"])
    if not message_action['token'] == os.environ['SLACK_VERIFICATION_TOKEN']:
        abort(400)

    if LOG_SERVER_RESPONSES:
        print(message_action)

    def get_username(message_action):
        if "user" in message_action["user"]:
            return message_action["user"]["user"]
        elif "username" in message_action["user"]:
            return message_action["user"]["username"]
        elif "name" in message_action["user"]:
            return message_action["user"]["name"]

    user_id = message_action["user"]["id"]
    user_name = get_username(message_action)

    if message_action["type"] == "block_actions":
        for action in message_action["actions"]:
            if action["type"] == "button":
                parsed = parse_callback_value(action["value"])
                if parsed[0] == 'new_tournament_dialog':
                    create_new_tournament_dialog(message_action["trigger_id"])
                elif parsed[0] == 'add_duel_dialog':
                    create_add_duel_dialog(message_action["trigger_id"], int(parsed[1]))
                elif parsed[0] == 'delete_duel':
                    delete_duel_and_update_message(message_action["channel"]["id"], int(parsed[1]), int(parsed[2]), message_action["message"]["ts"], user_name)
                elif parsed[0] == 'delete_tournament':
                    delete_tournament_and_remove_thread(message_action["channel"]["id"], int(parsed[1]))
                elif parsed[0] == 'tournament_report':
                    prepare_tournament_report(message_action["channel"]["id"], int(parsed[1]), user_id)
                elif parsed[0] == 'close_tournanent':
                    try_close_tournament(message_action["channel"]["id"], int(parsed[1]), user_id, user_name)
    elif message_action["type"] == "dialog_submission":
        if message_action["callback_id"] == 'new_tournament_submitted':
            create_new_tournament(message_action["channel"]["id"], user_id, user_name, message_action["submission"]["name"], date_token_now())
        if message_action["callback_id"] == 'new_duel_submitted':
            tournament_id = int(message_action["state"])
            duel_score = ((message_action["submission"]["p0"], int(message_action["submission"]["score0"])),
                          (message_action["submission"]["p1"], int(message_action["submission"]["score1"])))
            add_new_duel(message_action["channel"]["id"], user_id, tournament_id, duel_score, user_name)

    return ('', 200)