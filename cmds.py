import model

class Result:
    def __init__(self, ok, msg = ''):
        self.ok = ok
        self.msg = msg

    def __str__(self):
        return 'Result<{}, {}>'.format(self.ok, self.msg)

def on_create_tournament(user, name):
    m = model.Model()
    m.init()
    #r = m.add_tournament(user, name)
    #handle errors?
    #flood protection - can't create new tournament if the last was created in the last x seconds
    return Result(False, 'Unimplemented')

def on_delete_tournament(user):
    # protection: can't delete tournament after x seconds (hours?)
    return Result(False, 'No tournament to delete')

def on_list_tournaments():
    return Result(False, '[TODO]')

def on_add_duel(user, player1, player2, score):
    return Result(False, '[TODO]')

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

    elif cmds[0] == 'add-duel':
        if len(cmds) < 4:
            return Result(False, "'add-duel [player1] [player2] [score]' is missing arguments")
        if cmds[1][0] != '@' or cmds[2][0] != '@':
            return Result(False, "'add-duel [player1] [player2] [score]', the player must be a slack user starting with '@'")
        score = None
        try:
            score = tuple([int(x) for x in cmds[3].split('-')])
            if len(score) != 2:
                raise ValueError
        except ValueError:
            return Result(False, "'add-duel [player1] [player2] [score]', the score must be in a format '[number]-[number]'")
        return on_add_duel(user, cmds[1], cmds[2], score)


if __name__ == "__main__":
    print(handle_command('jakub.tyrcha', 'new'))
    print(handle_command('jakub.tyrcha', 'delete'))
    print(handle_command('jakub.tyrcha', 'help'))
    print(handle_command('jakub.tyrcha', 'add-duel @joe @jakub'))
    print(handle_command('jakub.tyrcha', 'add-duel @joe jakub 22'))
    print(handle_command('jakub.tyrcha', 'add-duel @joe @jakub 22'))
    print(handle_command('jakub.tyrcha', 'add-duel @joe @jakub 2-2'))
    print(handle_command('jakub.tyrcha', 'add-duel @joe @jakub a-a'))