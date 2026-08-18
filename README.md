# DiscordPYComponents

Discord Components V2 helper for discord.py.

Needs the `IS_COMPONENTS_V2` flag (`1 << 15`). That turns off normal content/embeds — everything goes through components.

```bash
pip install DiscordPYComponents
```

Python 3.10+, discord.py, aiohttp.

## Quick start

```python
from py_components import UI, TextDisplay, Button, ButtonStyle

@bot.command()
async def menu(ctx):
    ui = UI(
        TextDisplay("pick one"),
        Button("yes", custom_id="yes", style=ButtonStyle.SUCCESS),
        Button("no", custom_id="no", style=ButtonStyle.DANGER),
    )
    await ui.send(ctx)
```

## Components

**Content**

| class | type | what |
|-------|------|------|
| `TextDisplay` / `Text` | 10 | markdown text |
| `Thumbnail` | 11 | small image (section accessory) |
| `MediaGallery` | 12 | 1-10 images |
| `File` | 13 | attachment:// file |

**Layout**

| class | type | what |
|-------|------|------|
| `ActionRow` | 1 | up to 5 buttons or one select |
| `Section` | 9 | text + button/thumbnail accessory |
| `Separator` | 14 | spacing / divider |
| `Container` | 17 | groups stuff, optional accent colour |

**Interactive**

| class | type |
|-------|------|
| `Button` | 2 |
| `StringSelect` | 3 |
| `UserSelect` | 5 |
| `RoleSelect` | 6 |
| `MentionableSelect` | 7 |
| `ChannelSelect` | 8 |

## Buttons

```python
ButtonStyle.PRIMARY    # 1 blurple
ButtonStyle.SECONDARY  # 2 grey
ButtonStyle.SUCCESS    # 3 green
ButtonStyle.DANGER     # 4 red
ButtonStyle.LINK       # 5 needs url=
ButtonStyle.PREMIUM    # 6 needs sku_id=
```

```python
Button("click", custom_id="x", style=ButtonStyle.PRIMARY, emoji="🔥")
Button("docs", style=ButtonStyle.LINK, url="https://discord.com/developers/docs")
```

## Layout example

```python
from py_components import (
    UI, Container, TextDisplay, Section, Thumbnail,
    Separator, MediaGallery, Button, ButtonStyle
)

ui = UI(
    Container(
        TextDisplay("# status"),
        Separator(),
        Section(
            TextDisplay("**online** — 1204 members"),
            accessory=Thumbnail("https://cdn.discordapp.com/icons/.../icon.png"),
        ),
        MediaGallery("https://example.com/a.png", "https://example.com/b.png"),
        accent_color=0x5865F2,
    ),
    Button("refresh", custom_id="refresh"),
)
await ui.send(ctx)
```

Selects go in an ActionRow:

```python
from py_components import ActionRow, StringSelect, SelectOption

ui = UI(
    TextDisplay("colour?"),
    ActionRow(
        StringSelect(
            "colour",
            options=[
                SelectOption("red", "red"),
                SelectOption("blue", "blue"),
            ],
            placeholder="pick one",
        )
    ),
)
```

## Sending

```python
await ui.send(ctx)                          # channel
await ui.reply(interaction)                 # interaction response / followup
await ui.reply(interaction, ephemeral=True)
await ui.edit(interaction)                  # edit original / component message
```

Uses discord.py methods when it can, raw HTTP otherwise.

## Component ids

Ids get assigned automatically when you build a payload. Set your own if you need stable ones:

```python
TextDisplay("hi", id=10)
Button("x", custom_id="x", id=11)
```

```python
from py_components import find_by_id, replace_by_id, assign_ids

payload = ui.to_payload()
node = ui.get(10)                           # by id
payload = ui.replace(10, TextDisplay("updated", id=10))
```

Handy when editing a message and only swapping one piece.

## Modals

```python
from py_components import (
    Modal, Label, TextInput, TextInputStyle,
    RadioGroup, RadioGroupOption, Checkbox, FileUpload
)

modal = Modal(
    "report",
    "bug report",
    Label("what happened", TextInput("desc", style=TextInputStyle.PARAGRAPH)),
    Label("severity", RadioGroup("sev", [
        RadioGroupOption("low", "low"),
        RadioGroupOption("high", "high"),
    ])),
    Label("i can reproduce this", Checkbox("ok")),
    Label("screenshots", FileUpload("shots", min_values=0, required=False)),
)

@bot.tree.command(name="report")
async def report(interaction):
    await modal.open(interaction)
```

| class | type | notes |
|-------|------|-------|
| `Label` | 18 | wraps one control, label ≤45 |
| `TextInput` | 4 | short / paragraph |
| `FileUpload` | 19 | 0-10 files |
| `RadioGroup` | 21 | one choice, 2-10 options |
| `CheckboxGroup` | 22 | multi, 1-10 options |
| `Checkbox` | 23 | single yes/no |

Max 5 top-level components per modal.

## Callbacks

```python
from py_components import View, ButtonStyle

view = View()

async def on_yes(interaction):
    await interaction.response.send_message("ok", ephemeral=True)

view.add_button("yes", "yes", style=ButtonStyle.SUCCESS, callback=on_yes)
payload = view.to_payload()
```

```python
from py_components import default_registry

@default_registry.route("yes")
async def handle_yes(interaction):
    await interaction.response.send_message("ok")

await default_registry.dispatch(interaction.data["custom_id"], interaction)
```

## Emoji / defaults

```python
from py_components import make_emoji, UserSelect

Button("pepe", custom_id="p", emoji=make_emoji("pepe", id=123, animated=True))
Button("ok", custom_id="ok", emoji="✅")

UserSelect(
    "mods",
    default_values=[{"id": "111", "type": "user"}],
    min_values=1,
    max_values=3,
)
```

## Limits (discord side)

- V2 flag can't be removed once set
- no content / embeds / stickers / poll on V2 messages
- attachments only show if referenced by a File / media component
- 40 components max per message
- buttons need an ActionRow (or section accessory)
- one select per ActionRow

## License

MIT
