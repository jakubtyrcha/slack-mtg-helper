import model
import datetime
from processing import pretty_tournaments, pretty_duels

m = model.Model()
m.init()

def date_token_now():
    return datetime.datetime.now().isoformat()

class Result:
    def __init__(self, ok, msg = None):
        self.ok = ok
        self.msg = msg

    def __str__(self):
        return 'Result<{}, {}>'.format(self.ok, self.msg)

def on_create_tournament(user, name):
    m.add_tournament(name, user, date_token_now())
    return Result(True)

def on_delete_tournament(user):
    tid = m.last_tournament_id()
    if tid != -1:
        m.delete_tournament(tid, user, date_token_now())
    return Result(True)

def on_list_tournaments():
    return Result(True, pretty_tournaments(m.get_tournaments()))

def on_add_duel(user, player1, player2, score):
    tid = m.last_tournament_id()
    if tid != -1:
        m.add_duel(tid, player1, player2, "-".join([str(x) for x in score]), user, date_token_now())
    return Result(True)

def on_delete_duel(user, tid, id):
    m.delete_duel(tid, id, user, date_token_now())
    return Result(True)

def on_list_duels():
    tid = m.last_tournament_id()
    if tid != -1:
        return Result(True, pretty_duels(m.get_duels(tid)))
    return Result(False)

def handle_command(user, text):
    cmds = text.split()

    if cmds[0] == 'help':
        return Result(False, '[TODO]')

    elif cmds[0] == 'new':
        if len(cmds) < 2:
            return Result(False, "'new [name]' is missing an argument")
        return on_create_tournament(user, cmds[1][:32])

    elif cmds[0] == 'delete':
        return on_delete_tournament(user)

    elif cmds[0] == 'list-tournaments':
        return on_list_tournaments()

    elif cmds[0] == 'new-duel':
        if len(cmds) < 4:
            return Result(False, "'new-duel [player1] [player2] [score]' is missing arguments")
        if cmds[1][0] != '@' or cmds[2][0] != '@':
            return Result(False, "'new-duel [player1] [player2] [score]', the player must be a slack user starting with '@'")
        score = None
        try:
            score = tuple([int(x) for x in cmds[3].split('-')])
            if len(score) != 2:
                raise ValueError
        except ValueError:
            return Result(False, "'new-duel [player1] [player2] [score]', the score must be in a format '[number]-[number]'")
        return on_add_duel(user, cmds[1], cmds[2], score)

    elif cmds[0] == 'list-duels':
        return on_list_duels()


if __name__ == "__main__":
    try:
        print(handle_command('jakub.tyrcha', 'new'))
        print(handle_command('jakub.tyrcha', 'new DRAFT_0'))
        print(handle_command('jakub.tyrcha', 'delete'))
        print(handle_command('jakub.tyrcha', 'help'))
        print(handle_command('jakub.tyrcha', 'list-tournaments'))
        print(handle_command('jakub.tyrcha', 'new-duel @joe @jakub'))
        print(handle_command('jakub.tyrcha', 'new-duel @joe jakub 22'))
        print(handle_command('jakub.tyrcha', 'new-duel @joe @jakub 22'))
        print(handle_command('jakub.tyrcha', 'new-duel @joe @jakub 2-2'))
        print(handle_command('jakub.tyrcha', 'new-duel @joe @jakub a-a'))
        print(handle_command('jakub.tyrcha', 'new-duel @joe @jakub 3-2'))
        print(handle_command('jakub.tyrcha', 'new-duel @joe @jakub 2-2'))
        print(handle_command('jakub.tyrcha', 'new-duel @joe @jakub 1-1'))
        print(handle_command('jakub.tyrcha', 'list-duels'))
        m.destory_tables()
    except:
        m.destory_tables()