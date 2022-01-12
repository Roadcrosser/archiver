import disnake as discord

bot = discord.Client(
    intents=discord.Intents(guild_messages=True, members=True, guilds=True)
)

bot.start_timestamp = None


class Unroleban:
    def __init__(self):
        self.unset()

    def unset(self):
        self.is_set = False
        self.user_id = None
        self.time = None

    def set(self, user_id, time):
        self.is_set = True
        self.user_id = user_id
        self.time = time

    def diff(self, time):
        return (time - self.time).total_seconds()


LAST_UNROLEBAN = Unroleban()

DECISION_EMOTES = ["✅", "❎"]
