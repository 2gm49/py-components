# py-components

**Discord Components V2 for discord.py** — a lightweight helper library for building Discord UI components.

DISCLAIMER: THIS IS NOT COMPLETED AND LACKS FEATURES AND HAS BUGS.

PyPi: https://pypi.org/project/DiscordPYComponents/

## Installation

```bash
pip install DiscordPYComponents
```

## Requirements

- Python 3.10+
- discord.py
- aiohttp

## Usage

```python
from py_components import Button, Text, UI, ButtonStyle

@bot.command()
async def menu(ctx):
    ui = UI(
        Text("Choose an option:"),
        Button("Confirm", custom_id="confirm", style=ButtonStyle.success),
        Button("Cancel", custom_id="cancel", style=ButtonStyle.danger)
    )
    await ui.send(ctx)
```

### Button Styles

| Style                   | Colour |
|-------------------------|--------|
| `ButtonStyle.primary`   | Blue   |
| `ButtonStyle.secondary` | Grey   |
| `ButtonStyle.success`   | Green  |
| `ButtonStyle.danger`    | Red    |

### View & Callbacks

```python
from py_components import View

view = View()

async def on_click(interaction):
    await interaction.response.send_message("Clicked!")

view.add_button("Click Me", custom_id="btn", callback=on_click)
```

## License

MIT