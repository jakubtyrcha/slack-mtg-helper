class DialogBuilder:
    def __init__(self, slack_client, title, callback_id, state):
        self.slack_client = slack_client
        self.title = title
        self.callback_id = callback_id
        self.elements = []
        self.state = state

    def element(self, e):
        self.elements.append(e)
        return self

    def text(self, label, name, placeholder, limit = (0, 128)):
        return self.element({
            "label": label,
            "name": name,
            "type": "text",
            "min_length": limit[0],
            "max_length": limit[1],
            "placeholder": placeholder
        })

    def select(self, label, name, options):
        return self.element({
            "label": label,
            "type": "select",
            "name": name,
            "options": [{"label" : o[0], "value" : o[1]} for o in options]
        })

    def construct(self):
        return {
            "title": self.title,
            "submit_label": "Submit",
            "callback_id": self.callback_id,
            "elements": self.elements,
            "state" : self.state
        }

class CreateTournamentDialog(DialogBuilder):
    def __init__(self, slack_client, title, callback_id, state = ""):
        super().__init__(slack_client, title, callback_id, state)

        self.text("Name", "name", "tournament name", (3, 32))

class AddDuelDialog(DialogBuilder):
    def __init__(self, slack_client, title, callback_id, state = ""):
        super().__init__(slack_client, title, callback_id, state)

        scores = [(str(i), str(i)) for i in range(0, 9)]
        self.text("Player", "player_0", "@username", (2, 64)) \
            .select("Score", "score_0", scores)\
            .text("Player", "player_1", "@username", (2, 64)) \
            .select("Score", "score_1", scores)