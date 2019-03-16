from tabulate import tabulate
from itertools import groupby
from functools import reduce
from operator import add

from model import Duel, History

def pretty_tournaments(list):
    return tabulate([[x['id'], x['name'], x['date']] for x in list], headers = ['id', 'name', 'date'])

def pretty_duels(duels):                                                                                              
    def as_row(entry):                                                                                                
        return [str(entry.id), "{} {}-{} {}".format(entry.player0, entry.score[0], entry.score[1], entry.player1)]
    return tabulate([as_row(e) for e in duels], headers = ['id', 'score'])

def pretty_matrix(duels):
    users = set([x.player0 for x in duels] + [x.player1 for x in duels])
    users = sorted(list(users))
    user_index = dict([(u, i) for i, u in enumerate(users)])
    matrix = [[(0, 0) for _ in users] for _ in users]

    for r in duels:
        ai = user_index[r.player0]
        bi = user_index[r.player1]
        wa, g = matrix[ai][bi]
        wb, _ = matrix[bi][ai]
        g += r.score[0] + r.score[1]
        matrix[ai][bi] = (wa + r.score[0], g)
        matrix[bi][ai] = (wb + r.score[1], g)

    def tabulate_matrix(matrix, headers):
        matrix = [["{}/{}({})".format(x[0], x[1], 2*x[0]-x[1]) for x in r] for r in matrix]
        matrix = [[headers[i]] + r for i, r in enumerate(matrix)]
        headers = [''] + headers
        return tabulate(matrix, headers = headers)

    return tabulate_matrix(matrix, headers = users)

def pretty_table(duels):
    points = dict()

    def preprocessed(duels):
        def normal_form(e):
            if e.player0 < e.player1:
                return ((e.player0, e.player1), e.score)
            return ((e.player1, e.player0), (e.score[1], e.score[0]))

        duels = [normal_form(x) for x in duels]
        return [(g, reduce(lambda a, b: tuple(map(add, a, b)), [x[1] for x in k])) for g, k in
                groupby(duels, lambda x: x[0])]

    for pair, score in preprocessed(duels):
        points.setdefault(pair[0], 0)
        points.setdefault(pair[1], 0)
        if score[0] > score[1]:
            points[pair[0]] += 1
        elif score[1] > score[0]:
            points[pair[1]] += 1
    return tabulate(sorted(points.items(), key=lambda kv: -kv[1]), headers = ['player', 'points'])

def pretty_history(history, duels_dict):
    def as_row(entry):
        d = duels_dict[entry.did]
        misc = 'X' if d.deleted and entry.mod == '+' else ''
        return ["{}{}({})".format(entry.mod, entry.user, entry.id), "{} {}-{} {} {}".format(d.player0, d.score[0], d.score[1], d.player1, misc)]
    return tabulate([as_row(entry) for entry in history], headers = ['change', 'row'])

class BlocksBuilder:
    def __init__(self):
        self.blocks = []

    def divider(self):
        self.blocks.append({'type': 'divider'})
        return self

    def section(self, text):
        self.blocks.append({
            'type': 'section',
            'text': {
                'type': 'mrkdwn',
                'text': text
            }
        })
        return self

    def button(self, text, value):
        self.blocks.append({
            "type": "actions",
            "elements": [ {
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": text,
                    "emoji": True
                },
                "value": value
            }
        ]})
        return self

    def with_select(self, text, list):
        self.blocks[-1].update({
            "accessory": {
                "type": "static_select",
                "placeholder": {
                    "type": "plain_text",
                    "text": text,
                    "emoji": True
                },
                "options": [{
                    "text": {
                        "type": "plain_text",
                        "text": x[0],
                        "emoji": True
                    },
                    "value": x[1]
                } for x in list]
            }
        })

        return self

    def with_overflow(self, text, list):
        self.blocks[-1].update({
            "accessory": {
                "type": "overflow",
                "options": [{
                    "text": {
                        "type": "plain_text",
                        "text": x[0],
                        "emoji": True
                    },
                    "value": x[1]
                } for x in list]
            }
        })

        return self

    def with_select(self, text, list):
        return self.with_multi("static_select", text, list)

    def construct(self):
        return self.blocks

def markdown_tournaments_list(list):
    b = BlocksBuilder().section("*Tournaments*")

    for l in list:
        b.section('*{}*'.format(l['name'])).with_overflow("Options", [
            ("List duels", "list_duels;{}".format(str(l["id"]))),
            ("Add duel", "add_duel;{}".format(str(l["id"]))),
        ])

    b.button("Create tournament", "add_tournament")

    return b.construct()

if __name__ == "__main__":
    duels = [Duel({'score': '2-1', 'id': 1, 'player0': '@joe', 'deleted': False, 'player1': '@jakub', 'tid': 1}),
             Duel({'score': '2-1', 'id': 2, 'player0': '@joe', 'deleted': False, 'player1': '@jakub', 'tid': 1}),
             Duel({'score': '2-1', 'id': 4, 'player0': '@joe', 'deleted': False, 'player1': '@jakub', 'tid': 1}),
             Duel({'score': '2-1', 'id': 5, 'player0': '@joe', 'deleted': False, 'player1': '@stuart', 'tid': 1}),
             Duel({'score': '2-1', 'id': 6, 'player0': '@joe', 'deleted': False, 'player1': '@jakub', 'tid': 1})]
    # print(t.get_history_pretty())
    print(pretty_duels(duels))
    print(pretty_matrix(duels))
    print(pretty_table(duels))

    duels = [Duel({'score': '2-1', 'id': 1, 'player0': '@joe', 'deleted': False, 'player1': '@jakub', 'tid': 1}),
             Duel({'score': '2-1', 'id': 2, 'player0': '@joe', 'deleted': False, 'player1': '@jakub', 'tid': 1}),
             Duel({'score': '2-1', 'id': 4, 'player0': '@joe', 'deleted': True, 'player1': '@jakub', 'tid': 1}),
             Duel({'score': '2-1', 'id': 5, 'player0': '@joe', 'deleted': False, 'player1': '@stuart', 'tid': 1}),
             Duel({'score': '2-1', 'id': 6, 'player0': '@joe', 'deleted': False, 'player1': '@jakub', 'tid': 1})]
    history = [
        History({'date': '2019-08-22 11:12:11', 'id': 2, 'mod': '+', 'user': '@joe', 'did': 1, 'tid': 1}),
        History({'date': '2019-08-22 11:12:11', 'id': 3, 'mod': '+', 'user': '@joe', 'did': 2, 'tid': 1}),
        History({'date': '2019-08-22 11:12:11', 'id': 4, 'mod': '+', 'user': '@joe', 'did': 4, 'tid': 1}),
        History({'date': '2019-08-22 11:12:11', 'id': 5, 'mod': '+', 'user': '@joe', 'did': 5, 'tid': 1}),
        History({'date': '2019-08-22 11:12:11', 'id': 6, 'mod': '+', 'user': '@joe', 'did': 6, 'tid': 1}),
        History({'date': '2019-08-22 11:12:11', 'id': 7, 'mod': '-', 'user': '@joe', 'did': 4, 'tid': 1}),
    ]

    print(pretty_history(history, dict([(d.id, d) for d in duels])))