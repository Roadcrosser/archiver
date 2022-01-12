import disnake as discord
import aiohttp
import datetime
from config import COMMAND_NAME, GUILD_ID, PREFIXES, STAFF_ROLE, TOKEN
from logger import archive, has_role, is_rolebanned

from store import LAST_UNROLEBAN, bot


@bot.event
async def on_ready():
    print(f"Running on {bot.user.name}#{bot.user.discriminator} ({bot.user.id})")

    if not bot.start_timestamp:
        bot.session = aiohttp.ClientSession()
        bot.start_timestamp = datetime.datetime.utcnow().replace(
            tzinfo=datetime.timezone.utc
        )


@bot.event
async def on_message(message):

    if (
        message.author.bot
        or not message.content
        or not isinstance(message.channel, discord.abc.GuildChannel)
        or not message.guild.id == GUILD_ID
        or not message.channel.permissions_for(message.guild.me).send_messages
        or not has_role(message.author, STAFF_ROLE)
    ):
        return

    args = None
    cmd = None

    for p in PREFIXES:
        if message.content.lower().startswith(p.lower()):
            split = message.content[len(p) :].strip().split(None, 1)
            if split:
                cmd = split[0].lower()
            if len(split) > 1:
                args = split[1]
            if cmd != COMMAND_NAME.lower():
                continue
            break

    if cmd == COMMAND_NAME.lower():
        print(
            message.created_at.strftime("%Y-%m-%d %H:%M:%S")
            + " {0.guild.name}#{0.channel.name} - {0.author.name}: {0.content}".format(
                message
            )
        )

        await archive(message, args)


@bot.event
async def on_member_remove(member):
    if member.guild.id == GUILD_ID and is_rolebanned(member):
        LAST_UNROLEBAN.set(
            member.id, datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
        )


@bot.event
async def on_member_update(before, after):
    if (
        before.guild.id == GUILD_ID
        and is_rolebanned(before)
        and not is_rolebanned(after)
    ):
        LAST_UNROLEBAN.set(
            after.id, datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
        )


bot.run(TOKEN)
