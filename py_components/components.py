from .enums import ButtonStyle

class Text:
    def __init__(self, content):
        self.content = content

    def to_dict(self):
        return {
            "type": 10,
            "content": self.content
        }


class Button:
    def __init__(self, label, custom_id, style=ButtonStyle.primary):
        self.label = label
        self.custom_id = custom_id
        self.style = style

    def to_dict(self):
        return {
            "type": 2,
            "label": self.label,
            "custom_id": self.custom_id,
            "style": self.style
        }
