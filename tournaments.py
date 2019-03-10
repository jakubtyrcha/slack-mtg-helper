from tabulate import tabulate
from itertools import groupby
from functools import reduce
from operator import add

class DuelRow:
    def __init__(self, id, p0, p1, score):
        self.id = id
        self.score = score
        self.p0 = p0
        self.p1 = p1
        self.active = True

class Tournament:
    def __init__(self, id):
        self.date = ''
        self.id = id
        self.history = []
        self.rows = []

    def add_result(self, user, a, b, score):
        id = len(self.rows)
        self.history.append( ('+', user, id) )
        self.rows.append(DuelRow(id, a, b, score))

    def remove_result(self, user, id):
        if id < len(self.rows) and self.rows[id].active:
            self.history.append( ('-', user, id) )
            self.rows[id].active = False

    def get_history_pretty(self):
        def as_row(entry):
            mod, author, id = entry
            entry = self.rows[id]
            misc = '' if entry.active or mod == '-' else 'X'
            return ["{}{}({})".format(mod, author, id), "{} {}-{} {} {}".format(entry.p0, entry.score[0], entry.score[1], entry.p1, misc)]
        return tabulate([as_row(entry) for entry in self.history], headers = ['', 'row'])

    def get_duels_pretty(self):
        def as_row(entry):
            return [str(entry.id), "{} {}-{} {}".format(entry.p0, entry.score[0], entry.score[1], entry.p1)]
        return tabulate([as_row(e) for e in self.rows if e.active], headers = ['id', 'score'])

    def compile_matrix_pretty(self):
        users = set([x.p0 for x in self.rows] + [x.p1 for x in self.rows])
        users = sorted(list(users))
        user_index = dict([(u, i) for i, u in enumerate(users)])
        matrix = [[(0, 0) for _ in users] for _ in users]

        for r in self.rows:
            if r.active:
                ai = user_index[r.p0]
                bi = user_index[r.p1]
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

    def get_duels(self):
        def normal_form(e):
            if e.p0 < e.p1:
                return ((e.p0, e.p1), e.score)
            return ((e.p1, e.p0), (e.score[1], e.score[0]))
        duels = [normal_form(x) for x in self.rows if x.active]
        return [(g, reduce(lambda a, b: tuple(map(add, a, b)), [x[1] for x in k])) for g, k in groupby(duels, lambda x: x[0])]

    def get_table_pretty(self):
        points = dict()
        for pair, score in self.get_duels():
            points.setdefault(pair[0], 0)
            points.setdefault(pair[1], 0)
            if score[0] > score[1]:
                points[pair[0]] += 1
            elif score[1] > score[0]:
                points[pair[1]] += 1
        return tabulate(sorted(points.items(), key=lambda kv: -kv[1]), headers = ['player', 'points'])

if __name__ == "__main__":
    t = Tournament(0)
    t.add_result('@joe', '@joe', '@jakub', (2, 1))
    t.add_result('@joe', '@joe', '@jakub', (2, 1))
    t.add_result('@joe', '@joe', '@jakub', (2, 1))
    t.add_result('@joe', '@joe', '@jakub', (2, 1))
    t.add_result('@joe', '@joe', '@stuart', (2, 1))
    t.remove_result('@jakub', 3)
    print(t.get_history_pretty())
    print(t.get_duels_pretty())
    print(t.compile_matrix_pretty())
    print(t.get_table_pretty())