# DiscordPYComponents

**Discord Components V2 for discord.py** — a lightweight helper library for building rich, interactive messages with the modern Components V2 system.

> **Requires the `IS_COMPONENTS_V2` flag (`1 << 15`).**  
> When this flag is set, traditional `content` and `embeds` are disabled; all content must be sent as components.

PyPI: https://pypi.org/project/DiscordPYComponents/

Official Discord docs:
- [Components Overview](https://docs.discord.com/developers/components/overview)
- [Using Message Components](https://docs.discord.com/developers/components/using-message-components)
- [Component Reference](https://docs.discord.com/developers/components/reference)

## Installation

```bash
pip install DiscordPYComponents
```

## Requirements

- Python 3.10+
- discord.py (or any library that gives you a bot token + channel/interaction)
- aiohttp

## Quick start

```python
from py_components import (
    UI, TextDisplay, Button, ButtonStyle, Container, Separator, Section, Thumbnail
)

@bot.command()
async def menu(ctx):
    ui = UI(
        TextDisplay("# Welcome"),
        TextDisplay("Choose an option below:"),
        Button("Confirm", custom_id="confirm", style=ButtonStyle.SUCCESS),
        Button("Cancel", custom_id="cancel", style=ButtonStyle.DANGER),
    )
    await ui.send(ctx)
```

## Component types

### Content components

| Class | Type | Description |
|-------|------|-------------|
| `TextDisplay` / `Text` | 10 | Markdown text (1–4000 chars) |
| `Thumbnail` | 11 | Small image (Section accessory only) |
| `MediaGallery` | 12 | 1–10 images / media items |
| `File` | 13 | Displays an uploaded attachment |

### Layout components

| Class | Type | Description |
|-------|------|-------------|
| `ActionRow` | 1 | Holds up to 5 Buttons **or** one Select menu |
| `Section` | 9 | 1–3 TextDisplays + optional accessory (Button or Thumbnail) |
| `Separator` | 14 | Vertical padding / visual divider |
| `Container` | 17 | Groups children with optional accent colour bar |

### Interactive components

| Class | Type | Description |
|-------|------|-------------|
| `Button` | 2 | Clickable button |
| `StringSelect` | 3 | Dropdown of string options |
| `UserSelect` | 5 | Select users |
| `RoleSelect` | 6 | Select roles |
| `MentionableSelect` | 7 | Select users **or** roles |
| `ChannelSelect` | 8 | Select channels |

## Button styles

| Style | Value | Colour / behaviour |
|-------|-------|--------------------|
| `ButtonStyle.PRIMARY` | 1 | Blurple |
| `ButtonStyle.SECONDARY` | 2 | Grey |
| `ButtonStyle.SUCCESS` | 3 | Green |
| `ButtonStyle.DANGER` | 4 | Red |
| `ButtonStyle.LINK` | 5 | Grey – opens a URL (requires `url=`) |
| `ButtonStyle.PREMIUM` | 6 | Blurple – requires `sku_id=` |

```python
Button("Click me", custom_id="btn1", style=ButtonStyle.PRIMARY)
Button("Docs", style=ButtonStyle.LINK, url="https://discord.com/developers/docs")
Button("Buy", style=ButtonStyle.PREMIUM, sku_id="1234567890")
```

## Building a rich layout

```python
from py_components import (
    UI, Container, TextDisplay, Section, Thumbnail,
    Separator, SeparatorSpacing, MediaGallery, Button, ButtonStyle
)

ui = UI(
    Container(
        TextDisplay("# Server Status"),
        Separator(divider=True, spacing=SeparatorSpacing.SMALL),
        Section(
            TextDisplay("**Online** — 1 204 members"),
            TextDisplay("Peak today: 312"),
            accessory=Thumbnail("https://cdn.discordapp.com/icons/.../icon.png"),
        ),
        Separator(),
        MediaGallery(
            "https://example.com/chart1.png",
            "https://example.com/chart2.png",
        ),
        accent_color=0x5865F2,   # Discord blurple
    ),
    Button("Refresh", custom_id="refresh", style=ButtonStyle.PRIMARY),
)
await ui.send(ctx)
```

Top-level components can be mixed freely. The `UI` class automatically wraps loose `Button`s into `ActionRow`s (max 5 per row). Place select menus inside an explicit `ActionRow` yourself:

```python
from py_components import ActionRow, StringSelect, SelectOption

ui = UI(
    TextDisplay("Pick a colour:"),
    ActionRow(
        StringSelect(
            custom_id="colour",
            options=[
                SelectOption("Red", "red"),
                SelectOption("Green", "green"),
                SelectOption("Blue", "blue"),
            ],
            placeholder="Choose…",
        )
    ),
)
```

## View & callbacks

```python
from py_components import View, ButtonStyle

view = View()

async def on_confirm(interaction):
    await interaction.response.send_message("Confirmed!", ephemeral=True)

view.add_button("Confirm", custom_id="confirm", style=ButtonStyle.SUCCESS, callback=on_confirm)
view.add_button("Cancel", custom_id="cancel", style=ButtonStyle.SECONDARY)

# Send the payload yourself or combine with UI
payload = view.to_payload()
```

You can also use the decorator helper:

```python
from py_components import button, View

@button("Click Me", custom_id="my_btn")
async def on_click(interaction):
    await interaction.response.send_message("Clicked!")
```

## Global registry

```python
from py_components import default_registry

@default_registry.route("confirm")
async def handle_confirm(interaction):
    await interaction.response.send_message("OK")

# Later, in your interaction listener:
await default_registry.dispatch(interaction.data["custom_id"], interaction)
```

## File attachments

Upload the file with the message and reference it with the `File` component:

```python
from py_components import UI, File, TextDisplay

ui = UI(
    TextDisplay("Here is the report:"),
    File("report.pdf"),          # becomes attachment://report.pdf
)

# When calling the raw HTTP helper you would also pass the file bytes;
# with discord.py you can combine the payload with files=...
await ui.send(ctx)
```

## Responding to interactions

```python
@bot.event
async def on_interaction(interaction):
    if interaction.type.name == "component":
        custom_id = interaction.data.get("custom_id")
        # … route to your callbacks …
        # or reply with a new V2 message:
        ui = UI(TextDisplay(f"You pressed `{custom_id}`"))
        await ui.reply(interaction, ephemeral=True)
```

## Payload shape

Every payload produced by this library looks like:

```json
{
  "flags": 32768,
  "components": [
    { "type": 10, "content": "Hello" },
    {
      "type": 1,
      "components": [
        { "type": 2, "style": 1, "label": "OK", "custom_id": "ok" }
      ]
    }
  ]
}
```

You can also obtain the dict with `ui.to_payload()` / `view.to_payload()` and send it through any HTTP client or discord.py’s low-level methods.

## Limitations (Discord-side)

- Once a message is sent with `IS_COMPONENTS_V2` the flag cannot be removed.
- `content`, `embeds`, `stickers` and `poll` are disabled on V2 messages.
- Attachments only appear when referenced by a `File` or media component.
- Max 40 components per message.
- Buttons must live in an ActionRow (or as a Section accessory).
- Only one select menu per ActionRow.

## License

MIT
