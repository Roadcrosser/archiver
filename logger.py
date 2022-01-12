import zipfile
import httplib2
import textwrap
import asyncio
import re
from io import BytesIO

import disnake as discord

from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from oauth2client.service_account import ServiceAccountCredentials

from config import (
    DRIVE_FOLDER,
    MOD_CHANNEL,
    ROLEBAN_ROLE_IGNORE,
    ROLEBAN_ROLE_NAMES,
    UNROLEBAN_EXPIRY,
)
from store import DECISION_EMOTES, LAST_UNROLEBAN, bot


def has_role(member, role_id):
    return role_id in [r.id for r in member.roles]


def is_rolebanned(member, hard=True):
    roleban = [r for r in member.guild.roles if r.name in ROLEBAN_ROLE_NAMES]
    if roleban:
        if has_role(member, roleban[0].id):
            if hard:
                return (
                    len(
                        [
                            r
                            for r in member.roles
                            if not (r.managed or r.id in ROLEBAN_ROLE_IGNORE)
                        ]
                    )
                    == 2
                )
            return True


def textify_embed(embed, limit=40, padding=0, pad_first_line=True):
    text_proc = []
    title = ""
    if embed.title:
        title += embed.title
        if embed.url:
            title += " - "
    if embed.url:
        title += embed.url
    if not title and embed.author:
        title = embed.author.name
    if title:
        text_proc += [title, ""]
    if embed.description:
        text_proc += [embed.description, ""]
    if embed.thumbnail:
        text_proc += ["Thumbnail: " + embed.thumbnail.url, ""]
    for f in embed.fields:
        text_proc += [
            f.name
            + (
                ":"
                if not f.name.endswith(("!", ")", "}", "-", ":", ".", "?", "%", "$"))
                else ""
            ),
            *f.value.split("\n"),
            "",
        ]
    if embed.image:
        text_proc += ["Image: " + embed.image.url, ""]
    if embed.footer:
        text_proc += [embed.footer.text, ""]

    text_proc = [textwrap.wrap(t, width=limit) for t in text_proc]

    texts = []

    for tt in text_proc:
        if not tt:
            tt = [""]
        for t in tt:
            texts += [t + " " * (limit - len(t))]

    ret = " " * (padding * pad_first_line) + "╓─" + "─" * limit + "─╮"

    for t in texts[:-1]:
        ret += "\n" + " " * padding + "║ " + t + " │"

    ret += "\n" + " " * padding + "╙─" + "─" * limit + "─╯"

    return ret


async def log_whole_channel(channel, zip_files=False):
    st = ""

    if zip_files:
        b = BytesIO()
        z = zipfile.ZipFile(b, "w", zipfile.ZIP_DEFLATED)
        zipped_count = 0

    async for m in channel.history(limit=None):
        blank_content = True
        ts = "{:%Y-%m-%d %H:%M} ".format(m.created_at)
        padding = len(ts) + len(m.author.name) + 2
        add = ts
        if m.type == discord.MessageType.default:
            add += "{0.author.name}: {0.clean_content}".format(m)
            if m.clean_content:
                blank_content = False
        else:
            add += m.system_content

        for a in m.attachments:
            if not blank_content:
                add += "\n"
            add += " " * (padding * (not blank_content)) + "Attachment: " + a.filename
            if zip_files:
                fn = "{}-{}-{}".format(m.id, a.id, a.filename)
                async with bot.session.get(a.url) as r:
                    f = await r.read()

                z.writestr(fn, f)
                add += " (Saved as {})".format(fn)
                zipped_count += 1

            blank_content = False

        for e in m.embeds:
            if e.type == "rich":
                if not blank_content:
                    add += "\n"
                add += textify_embed(
                    e, limit=40, padding=padding, pad_first_line=not blank_content
                )
                blank_content = False

        if m.reactions:
            if not blank_content:
                add += "\n"
            add += " " * (padding * (not blank_content))
            add += " ".join(
                ["[{} {}]".format(str(r.emoji), r.count) for r in m.reactions]
            )
            blank_content = False

        add += "\n"
        st = add + st

    ret = st
    if zip_files:
        if zipped_count:
            z.writestr("log.txt", st)
            b.seek(0)
            ret = (ret, b)
        else:
            ret = (ret, None)

    return ret


def get_roleban_channels(guild):
    ret = [
        c.id
        for c in guild.text_channels
        if (c.overwrites_for(guild.default_role).read_messages == False)
        and any(
            [
                c.overwrites_for(r).read_messages
                for r in guild.roles
                if r.name in ROLEBAN_ROLE_NAMES
            ]
        )
    ]
    if not ret:
        return [0]
    return ret


async def get_members(message, args):
    user = []
    if args:
        user = message.guild.get_member_named(args)
        if not user:
            user = []
            arg_split = args.split()
            for a in arg_split:
                try:
                    a = int(a.strip("<@!#>"))
                except:
                    continue
                u = message.guild.get_member(a)
                if not u:
                    try:
                        u = await bot.fetch_user(a)
                    except:
                        pass
                if u:
                    user += [u]
        else:
            user = [user]

    return (user, None)


async def archive(message, args):
    roleban_channels = get_roleban_channels(message.guild)

    credentials = ServiceAccountCredentials.from_json_keyfile_name(
        "service_account.json", "https://www.googleapis.com/auth/drive"
    )
    credentials.authorize(httplib2.Http())
    gauth = GoogleAuth()
    gauth.credentials = credentials
    drive = GoogleDrive(gauth)
    folder = DRIVE_FOLDER

    try:
        await message.channel.trigger_typing()
    except:
        pass

    if message.channel.id in roleban_channels:
        out = await log_whole_channel(message.channel, zip_files=True)
        zipped_files = out[1]
        out = out[0]

        user = "unspecified (logged by {})".format(message.author.name)
        if (
            (not args)
            and LAST_UNROLEBAN.is_set
            and LAST_UNROLEBAN.diff(message.created_at) < UNROLEBAN_EXPIRY
        ):
            args = str(LAST_UNROLEBAN.user_id)
            LAST_UNROLEBAN.unset()

        if args:
            user = await get_members(message, args)
            if user[0]:
                user = " ".join(["{} {}".format(u.name, u.id) for u in user[0]])
            else:
                user = args

        fn = "{:%Y-%m-%d} {}".format(message.created_at, user)

        reply = "\👌\🏼\nArchived as: `{}.txt`".format(fn)

        out += "{:%Y-%m-%d %H:%M} {}: {}".format(
            message.created_at, bot.user.name, reply
        )

        modch = bot.get_channel(MOD_CHANNEL)

        f = drive.CreateFile(
            {
                "parents": [{"kind": "drive#fileLink", "id": folder}],
                "title": fn + ".txt",
            }
        )
        f.SetContentString(out)
        f.Upload()

        ret_string = (
            "{} archive saved as [`{}.txt`](https://drive.google.com/file/d/{})".format(
                message.channel.mention, fn, f["id"]
            )
        )

        if zipped_files:
            f_zip = drive.CreateFile(
                {
                    "parents": [{"kind": "drive#fileLink", "id": folder}],
                    "title": fn + " (files).zip",
                }
            )
            f_zip.content = zipped_files
            f_zip["mimeType"] = "application/zip"
            f_zip.Upload()

            ret_string += "\nFiles saved as [`{} (files).zip`](https://drive.google.com/file/d/{})".format(
                fn, f_zip["id"]
            )

        await message.channel.send(reply)
        await modch.send(
            embed=discord.Embed(description=ret_string, color=message.guild.me.color)
        )

        return True
    else:
        limit = 10
        query = "'{}' in parents".format(folder)
        args = re.sub("[^a-zA-Z0-9 ]", "", args) if args else None
        title = "Results"
        if not args:
            await message.channel.send(
                "Error: Unable to search archives. Please specify arguments."
            )
            return

        search_term = args
        if (
            args.startswith("search ")
            and message.channel.permissions_for(message.guild.me).add_reactions
        ):
            m = await message.channel.send(
                "**Warning:**\nAre you sure you want to search for `{}`?\n\n*Answering ❎ will search for `{}` instead.*".format(
                    args, args[7:]
                ),
            )
            for i in DECISION_EMOTES:
                await m.add_reaction(i)

            def check(reaction, user):
                return (
                    reaction.message.id == m.id
                    and user.id == message.author.id
                    and type(reaction.emoji) == str
                    and reaction.emoji.id in DECISION_EMOTES
                )

            try:
                reaction, user = await bot.wait_for(
                    "reaction_add", timeout=60, check=check
                )
            except asyncio.TimeoutError:
                pass

            if reaction and reaction.emoji.id == DECISION_EMOTES[1]:
                search_term = args[7:]

        query += " and title contains '{}'".format(search_term)
        title += " for " + search_term

        fl = drive.ListFile({"q": query}).GetList()
        fl_count = len(fl)
        unlisted_fl_count = fl_count - limit
        fl = fl[:limit]
        msg = "No Results."
        if fl:
            msg = "\n".join(
                [
                    "[`{title}`](https://drive.google.com/file/d/{id})".format(**f)
                    for f in fl
                ]
            )
            if unlisted_fl_count > 0:
                msg += f"\nand **{unlisted_fl_count}** more..."
        await message.channel.send(
            embed=discord.Embed(
                title=title,
                url="https://drive.google.com/drive/folders/{}".format(folder),
                description=msg,
                color=message.guild.me.color,
            )
        )

    return True
