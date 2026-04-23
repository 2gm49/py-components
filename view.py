from .components import Button

def button(label):
    def wrapper(func):
        func._button_label = label
        return func
    return wrapper


class View:
    def __init__(self):
        self.components = []
        self.registry = {}

    def add_button(self, label, custom_id, callback=None):
        btn = Button(label, custom_id)
        self.components.append(btn)

        if callback:
            self.registry[custom_id] = callback

        return btn

    def to_payload(self):
        return {
            "flags": 1 << 15,
            "components": [
                {
                    "type": 17,
                    "components": [c.to_dict() for c in self.components]
                }
            ]
        }
