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

class NewTournamentDialog(DialogBuilder):
    def __init__(self, slack_client, title, callback_id, state = ""):
        super().__init__(slack_client, title, callback_id, state)

        self.text("Name", "name", "tournament name", (3, 32))

class AddDuelDialog(DialogBuilder):
    def __init__(self, slack_client, title, callback_id, state = ""):
        super().__init__(slack_client, title, callback_id, state)

        scores = [(str(i), str(i)) for i in range(0, 9)]
        self.text("Player", "p0", "@username", (2, 64)) \
            .select("Score", "score0", scores)\
            .text("Player", "p1", "@username", (2, 64)) \
            .select("Score", "score1", scores)

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

    def with_confirm_simple(self, title, yes, no):
        self.blocks[-1]['elements'][-1].update({
            "confirm": {
                "title": {
                    "type": "plain_text",
                    "text": title
                },
                "confirm": {
                    "type": "plain_text",
                    "text": yes
                },
                "deny": {
                    "type": "plain_text",
                    "text": no
                }
            }
        })
        return self

    def with_confirm(self, title, text, yes, no):
        self.blocks[-1]['elements'][-1].update({
            "confirm": {
                "title": {
                    "type": "plain_text",
                    "text": title
                },
                "text": {
                    "type": "plain_text",
                    "text": text
                },
                "confirm": {
                    "type": "plain_text",
                    "text": yes
                },
                "deny": {
                    "type": "plain_text",
                    "text": no
                }
            }
        })
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

    def context(self, text):
        self.blocks.append({
            "type": "context",
            "elements": [{
                "type": "plain_text",
                "text": text,
                "emoji": True
            }]
        })
        return self

    def construct(self):
        return self.blocks
