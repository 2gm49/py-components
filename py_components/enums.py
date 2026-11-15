from enum import IntEnum


class ComponentType(IntEnum):
    ACTION_ROW = 1
    BUTTON = 2
    STRING_SELECT = 3
    TEXT_INPUT = 4
    USER_SELECT = 5
    ROLE_SELECT = 6
    MENTIONABLE_SELECT = 7
    CHANNEL_SELECT = 8
    SECTION = 9
    TEXT_DISPLAY = 10
    THUMBNAIL = 11
    MEDIA_GALLERY = 12
    FILE = 13
    SEPARATOR = 14
    CONTAINER = 17
    LABEL = 18
    FILE_UPLOAD = 19
    RADIO_GROUP = 21
    CHECKBOX_GROUP = 22
    CHECKBOX = 23


class ButtonStyle(IntEnum):
    PRIMARY = 1
    SECONDARY = 2
    SUCCESS = 3
    DANGER = 4
    LINK = 5
    PREMIUM = 6

    primary = PRIMARY
    secondary = SECONDARY
    success = SUCCESS
    danger = DANGER
    link = LINK
    premium = PREMIUM

    blurple = PRIMARY
    grey = SECONDARY
    gray = SECONDARY
    green = SUCCESS
    red = DANGER
    url = LINK


class TextInputStyle(IntEnum):
    SHORT = 1
    PARAGRAPH = 2

    short = SHORT
    paragraph = PARAGRAPH
    long = PARAGRAPH


class SeparatorSpacing(IntEnum):
    SMALL = 1
    LARGE = 2

    small = SMALL
    large = LARGE


class ChannelType(IntEnum):
    GUILD_TEXT = 0
    DM = 1
    GUILD_VOICE = 2
    GROUP_DM = 3
    GUILD_CATEGORY = 4
    GUILD_ANNOUNCEMENT = 5
    ANNOUNCEMENT_THREAD = 10
    PUBLIC_THREAD = 11
    PRIVATE_THREAD = 12
    GUILD_STAGE_VOICE = 13
    GUILD_DIRECTORY = 14
    GUILD_FORUM = 15
    GUILD_MEDIA = 16

    text = GUILD_TEXT
    voice = GUILD_VOICE
    category = GUILD_CATEGORY
    news = GUILD_ANNOUNCEMENT
    announcement = GUILD_ANNOUNCEMENT
    stage = GUILD_STAGE_VOICE
    forum = GUILD_FORUM
    media = GUILD_MEDIA


class InteractionResponseType(IntEnum):
    PONG = 1
    CHANNEL_MESSAGE_WITH_SOURCE = 4
    DEFERRED_CHANNEL_MESSAGE_WITH_SOURCE = 5
    DEFERRED_UPDATE_MESSAGE = 6
    UPDATE_MESSAGE = 7
    APPLICATION_COMMAND_AUTOCOMPLETE_RESULT = 8
    MODAL = 9
    LAUNCH_ACTIVITY = 12


class MessageFlags(IntEnum):
    SUPPRESS_EMBEDS = 1 << 2
    EPHEMERAL = 1 << 6
    SUPPRESS_NOTIFICATIONS = 1 << 12
    IS_COMPONENTS_V2 = 1 << 15


IS_COMPONENTS_V2 = 1 << 15
EPHEMERAL = 1 << 6
SUPPRESS_NOTIFICATIONS = 1 << 12

MAX_MESSAGE_COMPONENTS = 40
MAX_MODAL_COMPONENTS = 5
