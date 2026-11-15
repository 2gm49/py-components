# DiscordPYComponents

Discord Components V2 for discord.py.

PyPI: https://pypi.org/project/DiscordPYComponents/

Discord docs:
- https://docs.discord.com/developers/components/overview
- https://docs.discord.com/developers/components/reference

## Install

```bash
pip install DiscordPYComponents
```

Needs:
- Python 3.10+
- discord.py (or anything that gives you a token / interaction)
- aiohttp

```python
from py_components import (
    UI, TextDisplay, Button, ButtonStyle,
    Container, Section, Separator, ActionRow,
    StringSelect, SelectOption, Modal, Label, TextInput,
)
```

If your package folder is named differently, import from that name instead.

## How V2 works

Messages with Components V2 set `flags` to `IS_COMPONENTS_V2` (`1 << 15` / `32768`).

That means:
- no top-level `content` or `embeds`
- no stickers / poll on that message
- everything is components
- attachments only show if a `File` / media component points at them
- max 40 components per message
- once the flag is on a message, you can't turn it off

This library builds those payloads and can send them through discord.py or raw HTTP.

---

## UI

Main way to build and send a V2 message.

```python
ui = UI(
    TextDisplay("hello"),
    Button("ok", custom_id="ok", style=ButtonStyle.SUCCESS),
)
await ui.send(ctx)
```

### Methods

| method | what |
|--------|------|
| `UI(*components)` | start a builder |
| `ui.add(*components)` | append more |
| `ui.to_payload()` | `{"flags": 32768, "components": [...]}` |
| `ui.to_components()` | just the components list |
| `ui.get(id)` | find a component dict by numeric id |
| `ui.replace(id, component)` | payload with that id swapped |
| `await ui.send(target, ephemeral=False, files=None)` | channel or interaction |
| `await ui.reply(interaction, ...)` | same as send on an interaction |
| `await ui.edit(target, message=None)` | edit interaction original / a Message |
| `await ui.update(interaction)` | edit the message a button/select was used on |
| `ui.count()` | total components, nested ones included |
| `UI.from_payload(data)` | rebuild a UI from a raw payload or components list |

`send` / `reply` try discord.py first (`ctx.send`, `interaction.response.send_message`, `followup.send`). Falls back to raw HTTP if that fails.

```python
await ui.send(ctx)
await ui.reply(interaction)
await ui.reply(interaction, ephemeral=True)
await ui.edit(interaction)
await ui.edit(message)
```

Also: `await send_ui(target, ui)`, same as `ui.send(target)`.

Loose `Button`s are auto-wrapped into `ActionRow`s (5 per row). Loose selects get their own `ActionRow`.

`to_payload()` raises `ValueError` if the message would go over Discord's 40 component limit (nested components count too).

### Send options

```python
await ui.send(ctx, silent=True)                      # no push notification
await ui.send(ctx, allowed_mentions=discord.AllowedMentions.none())
await ui.reply(interaction, ephemeral=True)
```

Pings inside `TextDisplay` follow `allowed_mentions`.

---

## Content components

### TextDisplay / Text

Markdown text. Alias: `Text`.

```python
TextDisplay("**bold** and normal", id=1)
```

| arg | notes |
|-----|--------|
| `content` | required, 1–4000 chars |
| `id` | optional numeric id |

### Thumbnail

Small image for a Section accessory. Images only (incl gif/webp).

```python
Thumbnail("https://cdn.discordapp.com/...", description="icon", spoiler=False)
```

| arg | notes |
|-----|--------|
| `url` | required |
| `description` | alt text, max 1024 |
| `spoiler` | blur it |
| `id` | optional |

`url` can be `attachment://name.png` to use a file sent with the message.

### MediaGallery / MediaGalleryItem

1–10 media items.

```python
MediaGallery(
    "https://example.com/a.png",
    MediaGalleryItem("https://example.com/b.png", description="chart", spoiler=True),
)
```

| arg | notes |
|-----|--------|
| `*items` | urls and/or `MediaGalleryItem` |
| `id` | optional |

`MediaGalleryItem(url, description=None, spoiler=False)`. Description max 1024.

```python
gallery = MediaGallery("https://example.com/a.png")
gallery.add("https://example.com/b.png")
```

### File

Shows an uploaded attachment. Upload the file with the message; reference it here.

```python
File("report.pdf")                 # -> attachment://report.pdf
File("attachment://report.pdf", spoiler=True)
```

| arg | notes |
|-----|--------|
| `filename` | name or `attachment://name` |
| `spoiler` | blur it |
| `id` | optional |

When you read a File back from a message (`UI.from_payload`), `.name` and `.size` are filled in from Discord.

---

## Layout components

### ActionRow

Holds up to 5 buttons **or** one select. Mixing them raises `ValueError`.

```python
ActionRow(
    Button("a", custom_id="a"),
    Button("b", custom_id="b"),
)
ActionRow(StringSelect("pick", options=[...]))
```

### Section

1–3 TextDisplays + optional accessory (Button or Thumbnail). Plain strings are turned into TextDisplays.

```python
Section(
    TextDisplay("**title**"),
    TextDisplay("body text"),
    accessory=Thumbnail("https://..."),
)
```

### Separator

Spacing between components.

```python
Separator()  # divider on, small spacing
Separator(divider=False, spacing=SeparatorSpacing.LARGE)
```

| arg | notes |
|-----|--------|
| `divider` | show a line, default True |
| `spacing` | `SeparatorSpacing.SMALL` (1) or `LARGE` (2) |
| `id` | optional |

### Container

Groups children. Optional left accent colour (like embeds) and spoiler.

```python
Container(
    TextDisplay("# header"),
    Separator(),
    TextDisplay("body"),
    accent_color=0x5865F2,
    spoiler=False,
)
```

Children can be ActionRow, TextDisplay, Section, MediaGallery, Separator, File. Anything else raises `ValueError`.

`accent_color` takes an int (`0x000000`–`0xFFFFFF`) or a `discord.Colour`. `accent_colour=` works too.

```python
c = Container(TextDisplay("x"), accent_color=discord.Colour.blurple())
c.add(Separator(), TextDisplay("more"))
```

---

## Buttons

```python
Button(
    "label",
    custom_id="id",
    style=ButtonStyle.PRIMARY,
    emoji="🔥",           # or make_emoji(...)
    disabled=False,
    id=None,
)
```

| style | value | needs |
|-------|-------|--------|
| `PRIMARY` | 1 | custom_id |
| `SECONDARY` | 2 | custom_id |
| `SUCCESS` | 3 | custom_id |
| `DANGER` | 4 | custom_id |
| `LINK` | 5 | url= |
| `PREMIUM` | 6 | sku_id= |

Lowercase aliases work too: `ButtonStyle.primary`, and the discord.py names `blurple`, `grey`, `green`, `red`, `url`.

```python
Button("docs", style=ButtonStyle.LINK, url="https://discord.com/developers/docs")
Button("buy", style=ButtonStyle.PREMIUM, sku_id="1234567890")
Button("nope", custom_id="x", disabled=True)
```

Must sit in an ActionRow or as a Section accessory. UI auto-wraps loose buttons.

Rules (checked when you create the button):
- needs a `label` or an `emoji` (except PREMIUM)
- label max 80, custom_id 1–100, url max 512
- LINK: `url`, no `custom_id`
- PREMIUM: `sku_id` only, no label, emoji, url or custom_id

---

## Selects

All selects need a `custom_id`. In messages they go inside an ActionRow (one select per row). In modals they go inside a Label.

Shared rules: `placeholder` max 150, `min_values` 0–25, `max_values` 1–25, `min_values <= max_values`. If you set `required=True`, `min_values` must be at least 1.

### SelectOption (StringSelect only)

```python
SelectOption(
    "Red",
    "red",
    description="the red one",
    emoji="🔴",
    default=False,
)

SelectOption("Red")   # value defaults to the label
```

Label, value and description max 100.

### StringSelect

```python
StringSelect(
    "colour",
    options=[
        SelectOption("red", "red"),
        SelectOption("blue", "blue"),
    ],
    placeholder="pick one",
    min_values=1,
    max_values=1,
    disabled=False,
    required=None,   # modals only
)
```

1–25 options with unique values. `max_values` can't be more than the number of options. Plain strings work as options: `StringSelect("colour", ["red", "blue"])`.

### UserSelect / RoleSelect / MentionableSelect / ChannelSelect

```python
UserSelect(
    "mods",
    placeholder="pick mods",
    min_values=1,
    max_values=3,
    default_values=[
        {"id": "111111111111111111", "type": "user"},
    ],
    required=None,
    disabled=False,
)

RoleSelect("roles", min_values=0, max_values=5)
MentionableSelect("who")
ChannelSelect(
    "channel",
    channel_types=[0, 2, 5],  # text, voice, announce — discord channel type ints
)
```

`default_values` takes any of:

```python
from py_components import SelectDefaultValue, ChannelType

UserSelect("u", default_values=[member, 1234567890])            # objects or ids
RoleSelect("r", default_values=[SelectDefaultValue.role(role)])
MentionableSelect("m", default_values=[
    SelectDefaultValue.user(111),
    SelectDefaultValue.role(222),
])
ChannelSelect("c", channel_types=[ChannelType.text, ChannelType.voice],
              default_values=[channel])
{"id": "<snowflake>", "type": "user"}                            # raw dicts still work
```

The number of defaults has to fit between `min_values` and `max_values`, and the type has to match the select (MentionableSelect needs `SelectDefaultValue.user/role` for bare ids).
`required` only matters in modals. `disabled` only in messages (modals error if disabled).

---

## Emoji helper

```python
from py_components import make_emoji

make_emoji("🔥")
make_emoji("pepe", id=123456789012345678, animated=True)
```

Anywhere an emoji is accepted you can pass a unicode string, a `<:name:id>` / `<a:name:id>` string, a dict, or a discord.py `Emoji` / `PartialEmoji`.

Buttons and SelectOptions also take a plain unicode string:

```python
Button("ok", custom_id="ok", emoji="✅")
SelectOption("fire", "fire", emoji="🔥")
```

---

## Component ids

Every component can take `id=` (int). If you don't set one, payloads from UI / View / Modal get sequential ids filled in automatically.

```python
TextDisplay("hi", id=10)
Button("x", custom_id="x", id=11)
```

```python
from py_components import assign_ids, find_by_id, replace_by_id

payload = ui.to_payload()
node = ui.get(10)
payload = ui.replace(10, TextDisplay("updated", id=10))

# or on raw dict trees
assign_ids(payload["components"], start=1)
found = find_by_id(payload["components"], 10)
replace_by_id(payload["components"], 10, TextDisplay("x", id=10).to_dict())
```

Use this when editing a message and only changing one piece.

Ids are only added to components, never to media gallery items.

### Reading components back

```python
from py_components import UI, component_from_dict

ui = UI.from_payload(raw_message_dict)       # or a components list
first = component_from_dict(raw_message_dict["components"][0])
```

Every component class builds from its raw dict. Component types this library doesn't know yet come back as `UnknownComponent`, which keeps the raw data and sends it back unchanged.

---

## Modals

```python
from py_components import (
    Modal, Label, TextInput, TextInputStyle,
    RadioGroup, RadioGroupOption, CheckboxGroup, GroupOption, Checkbox,
    FileUpload, StringSelect, SelectOption,
)

modal = Modal(
    "report_modal",
    "bug report",
    Label(
        "what happened",
        TextInput("desc", style=TextInputStyle.PARAGRAPH, max_length=1000),
        description="as much detail as you can",
    ),
    Label(
        "severity",
        RadioGroup("sev", [
            RadioGroupOption("low", "low"),
            RadioGroupOption("high", "high", default=True),
        ]),
    ),
    Label(
        "areas",
        CheckboxGroup("areas", [
            GroupOption("ui", "ui"),
            GroupOption("api", "api"),
        ], min_values=1, max_values=2),
    ),
    Label("i can reproduce this", Checkbox("repro")),
    Label(
        "screenshots",
        FileUpload("shots", min_values=0, max_values=3, required=False, file_types=["image"]),
    ),
)

@bot.tree.command(name="report")
async def report(interaction):
    await modal.open(interaction)
```

Max **5** top-level components. Top-level must be `Label` or `TextDisplay`. Interactive controls go **inside** a Label. Components inside a modal can't be `disabled`. All of this is checked when you build the modal.

`modal.open(interaction)` must be the first response to the interaction. It raises if you've already responded.

### Modal

```python
Modal(custom_id, title, *components)
modal.add(*components)
modal.to_dict()       # data object
modal.to_response()   # {"type": 9, "data": ...}
await modal.open(interaction)
```

Title max 45 chars. custom_id 1–100.

### Label

```python
Label("visible label", child_component, description="optional helper text")
```

Label text max 45. Description max 100. One child: TextInput, any select, FileUpload, RadioGroup, CheckboxGroup or Checkbox.

### TextInput

```python
TextInput(
    "field_id",
    style=TextInputStyle.SHORT,      # or PARAGRAPH (2)
    min_length=0,
    max_length=4000,
    required=True,
    value="prefill",
    placeholder="type here",
)
```

min_length 0–4000, max_length 1–4000, value max 4000, placeholder max 100.

`TextInput(..., label="...")` still works for old ActionRow modals but gives a `DeprecationWarning`. Use `Label` instead.

### FileUpload

```python
FileUpload(
    "files",
    min_values=0,
    max_values=10,
    required=True,
    file_types=["image", "video", "audio", ".pdf"],  # optional filter
)
```

Up to 10 files, up to 10 `file_types` (`image`, `video`, `audio` or a `.ext`). File size follows the user's own upload limit.

### RadioGroup / CheckboxGroup / Checkbox

```python
# one choice, 2–10 options
RadioGroup("sev", [RadioGroupOption("low", "low"), RadioGroupOption("high", "high")], required=True)

# multi, 1–10 options
CheckboxGroup(
    "tags",
    [GroupOption("a", "a"), GroupOption("b", "b")],
    min_values=1,
    max_values=2,
    required=True,
)

# single yes/no, label comes from the Label wrapper
Checkbox("agree", default=False)
```

A Checkbox can't be required. For a "must tick" box, use a CheckboxGroup with one option and `required=True`. RadioGroup allows one `default` option.

`GroupOption` / `RadioGroupOption` / `CheckboxGroupOption` are the same thing:

```python
GroupOption("label", "value", description="...", default=False)
```

Selects also work inside Label in modals (StringSelect, UserSelect, etc.).

### Reading a modal submit

```python
from py_components import ModalSubmit

@bot.event
async def on_interaction(interaction):
    if interaction.type.name == "modal_submit" and interaction.data["custom_id"] == "apply":
        form = ModalSubmit(interaction)

        why = form.text("why")                 # TextInput -> str
        level = form.get("exp", "none")        # RadioGroup -> str or None
        teams = form.selected("teams")         # CheckboxGroup / selects -> list[str]
        agreed = form.checked("rules")         # Checkbox -> bool
        files = form.attachments("shots")      # FileUpload -> attachment dicts
        refs = form.users("ref")               # UserSelect -> resolved user dicts

        await interaction.response.send_message(f"thanks, got {len(files)} files", ephemeral=True)
```

| method | returns |
|--------|---------|
| `form["id"]` | raw value |
| `form.get("id", default)` | value, or default if empty |
| `form.text("id")` | str |
| `form.checked("id")` | bool |
| `form.selected("id")` | list of str |
| `form.attachments("id")` | uploaded attachment dicts |
| `form.users / members / roles / channels("id")` | resolved objects for selects |
| `form.values()` | dict of every custom_id and value |
| `form.fields` | `SubmittedField` objects (custom_id, type, id, value, raw) |

Works with a discord.py `Interaction` or a raw interaction dict. `parse_modal(x)` is the same as `ModalSubmit(x)`.

---

## View + callbacks

```python
from py_components import View, ButtonStyle

view = View()

async def on_yes(interaction):
    await interaction.response.send_message("ok", ephemeral=True)

view.add_button("yes", "yes", style=ButtonStyle.SUCCESS, callback=on_yes)
view.add_button("no", "no", style=ButtonStyle.SECONDARY)

payload = view.to_payload()
# send payload yourself or merge into a UI
```

```python
view.add_component(some_component, callback=coro)  # registers by custom_id
await view.dispatch(custom_id, interaction)
```

### @button decorator

```python
from py_components import button

@button("click me", custom_id="my_btn", style=ButtonStyle.PRIMARY)
async def on_click(interaction):
    await interaction.response.send_message("clicked")

# sets on_click._button_label / _button_custom_id / _button_style
```

### Registry

Global custom_id → callback map.

```python
from py_components import Registry, default_registry

@default_registry.route("yes")
async def handle_yes(interaction):
    await interaction.response.send_message("ok")

# or
default_registry.register("no", handle_no)

await default_registry.dispatch(interaction.data["custom_id"], interaction)
default_registry.clear()
```

You can make your own `Registry()` instance too.

Wire it up in your bot:

```python
@bot.event
async def on_interaction(interaction):
    if interaction.type.name in ("component", "modal_submit"):
        await default_registry.dispatch_interaction(interaction)
```

`dispatch_interaction` reads the custom_id for you and returns False if nothing matched. Views have the same method, plus `view.add_select(select, callback=...)`.

### Reading a button or select

```python
from py_components import ComponentClick

click = ComponentClick(interaction)
click.custom_id      # "range"
click.values         # ["7d"] for selects, [] for buttons
click.value          # first value or None
click.is_select      # True
click.resolved       # users / roles / channels for entity selects
```

Answer by editing the message in place:

```python
await new_ui.update(interaction)
```

---

## Low-level HTTP

Used internally. Available if you're not on discord.py send paths.

```python
from py_components import send_message, edit_message, respond_interaction, open_modal

await send_message(channel_id, bot_token, payload, files=None)
await edit_message(channel_id, message_id, bot_token, payload)
await respond_interaction(application_id, interaction_token, bot_token, payload, type=4)
await open_modal(interaction_id, interaction_token, modal_data)
```

`files` for `send_message` is a list of dicts: `{"fp": fileobj, "filename": "x.png", "content_type": "..."}`.

API base: `https://discord.com/api/v10`.

---

## Enums / constants

```python
from py_components import (
    ComponentType,             # ACTION_ROW=1, BUTTON=2, ... CHECKBOX=23
    ButtonStyle,               # PRIMARY..PREMIUM
    TextInputStyle,            # SHORT=1, PARAGRAPH=2
    SeparatorSpacing,          # SMALL=1, LARGE=2
    ChannelType,               # GUILD_TEXT=0, GUILD_VOICE=2, ... (for ChannelSelect)
    InteractionResponseType,   # UPDATE_MESSAGE=7, MODAL=9, ...
    MessageFlags,              # EPHEMERAL, SUPPRESS_NOTIFICATIONS, IS_COMPONENTS_V2
    IS_COMPONENTS_V2,          # 1 << 15
    EPHEMERAL,                 # 1 << 6
    SUPPRESS_NOTIFICATIONS,    # 1 << 12
    MAX_MESSAGE_COMPONENTS,    # 40
    MAX_MODAL_COMPONENTS,      # 5
)
```

---

## Full message example

```python
from py_components import (
    UI, Container, TextDisplay, Section, Thumbnail, Separator,
    SeparatorSpacing, MediaGallery, ActionRow, Button, ButtonStyle,
    StringSelect, SelectOption, File,
)

ui = UI(
    Container(
        TextDisplay("# server status"),
        Separator(spacing=SeparatorSpacing.SMALL),
        Section(
            TextDisplay("**online** — 1204 members"),
            TextDisplay("peak today: 312"),
            accessory=Thumbnail("https://cdn.discordapp.com/icons/ID/icon.png"),
        ),
        Separator(divider=True),
        MediaGallery(
            "https://example.com/chart1.png",
            "https://example.com/chart2.png",
        ),
        accent_color=0x5865F2,
    ),
    ActionRow(
        StringSelect(
            "range",
            options=[
                SelectOption("24h", "24h"),
                SelectOption("7d", "7d"),
                SelectOption("30d", "30d"),
            ],
            placeholder="range",
        )
    ),
    Button("refresh", custom_id="refresh", style=ButtonStyle.PRIMARY, emoji="🔄"),
    Button("docs", style=ButtonStyle.LINK, url="https://example.com/docs"),
    File("report.pdf"),
)

await ui.send(ctx)
```

---

## Full modal example

```python
from py_components import (
    Modal, Label, TextInput, TextInputStyle,
    RadioGroup, RadioGroupOption, CheckboxGroup, GroupOption,
    Checkbox, FileUpload, UserSelect,
)

modal = Modal(
    "apply",
    "staff application",
    Label("why us", TextInput("why", style=TextInputStyle.PARAGRAPH, min_length=50)),
    Label(
        "experience",
        RadioGroup("exp", [
            RadioGroupOption("none", "none"),
            RadioGroupOption("some", "some"),
            RadioGroupOption("lots", "lots"),
        ]),
    ),
    Label(
        "teams",
        CheckboxGroup("teams", [
            GroupOption("mod", "mod"),
            GroupOption("events", "events"),
            GroupOption("tech", "tech"),
        ], min_values=1, max_values=3),
    ),
    Label("referral", UserSelect("ref", min_values=0, max_values=1, required=False)),
    Label("i read the rules", Checkbox("rules")),
)

await modal.open(interaction)
```

---

## Limits (discord)

- V2 flag is permanent on that message
- no content / embeds / stickers / poll with V2
- attachments need a File or media component
- 40 components max per message
- buttons: ActionRow or Section accessory
- one select per ActionRow
- modals: max 5 top-level components, title ≤45
- Label label ≤45, description ≤100
- Button label ≤80, custom_id ≤100, url ≤512
- select placeholder ≤150, 0–25 values, 25 options
- TextDisplay ≤4000, thumbnail/gallery descriptions ≤1024
- component `id` is a 32-bit int, unique in the message

The library checks these when you build components, so mistakes show up as a `ValueError` in your code instead of a 400 from Discord.

## Changelog

### 1.4.0
- Read components back: `UI.from_payload`, `component_from_dict`, `UnknownComponent` for future types
- `ModalSubmit` / `parse_modal` to read modal answers, including file uploads and resolved users, roles and channels
- `ComponentClick` / `parse_component` for buttons and selects
- `Registry.dispatch_interaction` and `View.dispatch_interaction` for components and modals
- `SelectDefaultValue` and object/id support for select `default_values`
- `ChannelType`, `InteractionResponseType`, `MessageFlags` enums
- `ui.send(silent=True, allowed_mentions=...)`, `ui.update()`, `ui.count()`
- Loose selects in a `UI` or `View` are wrapped in an ActionRow automatically
- Validation for every Discord limit: 40 component cap, placeholder, option counts, min/max values, file types, button rules, container and section children, modal children, accent colour range
- Emoji accepts `<:name:id>` strings and discord.py emoji objects; Container accepts `discord.Colour`
- `TextInput(label=...)` kept for legacy modals with a deprecation warning
- Fixed: ids were being added to media gallery items

## License

MIT
