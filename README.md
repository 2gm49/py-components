# py-components

**py-components** is a lightweight Python library that provides helpers for building Discord Components (Buttons, Select Menus, Action Rows) for use with `discord.py`.

It is designed to simplify the creation and handling of Discord UI components while keeping the API clean, minimal, and easy to extend.

---

## ✨ Features

- Simple Discord Components V2 wrapper
- Easy-to-use Button, Select Menu, and Action Row builders
- Async-friendly design
- Clean and readable API
- Built to integrate with `discord.py`

---

## 📦 Installation

```bash
pip install py-components
````

---

## ⚙️ Requirements

* Python 3.10+
* discord.py (latest recommended)
* aiohttp

---

## 🚀 Quick Start

### Creating a Button

```python
from py_components import Button, ActionRow

button = Button(
    label="Click Me",
    style="primary",
    custom_id="click_me_button"
)

row = ActionRow(components=[button])
```

---

## 🧠 Handling Interactions

```python
from py_components import Button

button = Button(
    label="Hello",
    style="success",
    custom_id="hello_button"
)

async def handle_interaction(interaction):
    await interaction.response.send_message("You clicked the button!")
```

---

## 🧩 Components

### 🔘 Buttons

Supported styles:

* primary
* secondary
* success
* danger

```python
Button(
    label="Delete",
    style="danger",
    custom_id="delete_btn"
)
```

---

### 📋 Select Menus

```python
from py_components import SelectMenu

menu = SelectMenu(
    custom_id="menu_example",
    options=[
        {"label": "Option 1", "value": "opt1"},
        {"label": "Option 2", "value": "opt2"}
    ]
)
```

---

### 📦 Action Rows

Used to group components together.

```python
from py_components import ActionRow

row = ActionRow(components=[button, menu])
```

---

## 📁 Example Usage

```python
from py_components import Button, ActionRow, SelectMenu

button = Button(
    label="Click Me",
    style="primary",
    custom_id="btn_1"
)

menu = SelectMenu(
    custom_id="menu_1",
    options=[
        {"label": "Red", "value": "red"},
        {"label": "Blue", "value": "blue"}
    ]
)

row = ActionRow(components=[button, menu])
```

---

## 🛣 Roadmap

* Modal support
* Full discord.py integration helpers
* Prebuilt UI templates
* Advanced component event handling
* Stronger typing + validation
* More Discord component types support

---

## 📌 Project Structure

```
py-components/
├── py_components/
│   ├── __init__.py
│   ├── buttons.py
│   ├── select.py
│   └── components.py
├── README.md
├── pyproject.toml
└── LICENSE
```

---

## 📜 License

MIT License

---

## 💡 Notes

This library is a helper layer for building Discord UI components more efficiently. It does not replace `discord.py`, but extends it with easier component creation utilities.

```
```
--