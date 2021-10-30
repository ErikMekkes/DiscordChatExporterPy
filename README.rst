DiscordChatExporterPy
=====================

|version| |license| |language|

.. |license| image:: https://img.shields.io/pypi/l/chat-exporter

.. |version| image:: https://img.shields.io/pypi/v/chat-exporter

.. |language| image:: https://img.shields.io/github/languages/top/mahtoid/discordchatexporterpy

DiscordChatExporterPy is a Python plugin for your discord.py bot, allowing you to export a discord channels history within a guild.

! WARNING !
-----------
This fork adds a local_export function that additionally performs local downloads of any resources linked in a discord channels history.
This creates a more complete export for longer useability by no longer relying on external resources.

THIS HAS SEVERE SECURITY IMPLICATIONS if not used in a well controlled environment. TO MITIGATE THIS:
1 - You need to control what content your users submit to channels.
2 - You need to control who has access to the export functionality.
3 - You need to protect the machine and your network from possible damage by downloading content.
4 - You need to ensure anyone or anything with access to the files on the machine is prevented from, or is extremely careful with the execution of downloaded content.

YOU ALSO NEED to respect PRIVACY and COPYRIGHT concerns in use of this functionality. Users on your Discord server are already expected to comply with these in the usual manner through Discord's Terms of Service. But use of this function places similar responsibilities on you as a data holder.

Other Minor Additions
---------------------
- Support for playable gifs / video / gifv from embeds in the export.
- prettified html output that is a bit more human readable.

Usage
-----
**Basic Usage**

.. code:: py
    
    import discord
    import chat_exporter
    from discord.ext import commands

    intents = discord.Intents.default()
    intents.members = True
    
    bot = commands.Bot(command_prefix="!", intents=intents)
    
    
    @bot.event
    async def on_ready():
        print("Live: " + bot.user.name)
        chat_exporter.init_exporter(bot)
    
    
    @bot.command()
    async def save(ctx):
        await chat_exporter.quick_export(channel, guild)
    
    if __name__ == "__main__":
        bot.run("BOT_TOKEN_HERE")

*Optional: If you want the transcript to display Members (Role) Colours then enable the Members Intent.
Passing 'guild' is optional and is only necessary when using enhanced-dpy.*

**Customisable Usage**

.. code:: py

    import io

    ...

    @bot.command()
    async def save(ctx, limit: int, tz_info):
        transcript = await chat_exporter.export(ctx.channel, guild, limit, tz_info)

        if transcript is None:
            return

         transcript_file = discord.File(io.BytesIO(transcript.encode()),
                                        filename=f"transcript-{ctx.channel.name}.html")

        await ctx.send(file=transcript_file)

*Optional: limit and tz_info are both optional, but can be used to limit the amount of messages transcribed or set a 'local' (pytz) timezone for
the bot to transcribe message times to. Passing 'guild' is optional and is only necessary when using enhanced-dpy.*

**Raw Usage**

.. code:: py

    import io

    ...

    @bot.command()
    async def purge(ctx, tz_info):
        deleted_messages = await ctx.channel.purge()

        transcript = await chat_exporter.raw_export(channel, guild, deleted_messages, tz_info)

        if transcript is None:
            return

         transcript_file = discord.File(io.BytesIO(transcript.encode()),
                                        filename=f"transcript-{ctx.channel.name}.html")

        await ctx.send(file=transcript_file)

*Optional: tz_info is optional, but can be used to set a 'local' (pytz) timezone for the bot to transcribe message times to.
Passing 'guild' is optional and is only necessary when using enhanced-dpy.*

**Local Export Usage*

.. code:: py

    @bot.command()
    async def save(ctx):
        export_dir_name = "export_folder"
        await chat_exporter.local_export(ctx.channel, guild, limit, timezone, export_dir_name)
        return

*The export directory name that files get placed in is relative to the main entry point of the python program. See comments snippets above for guild, limit and timezone argument explanations.

Attributions
------------
Original code as https://github.com/mahtoid/DiscordChatExporterPy by https://github.com/mahtoid
*This project borrows CSS and HTML code from* `Tyrrrz's C# DiscordChatExporter <https://github.com/Tyrrrz/DiscordChatExporter/>`_ *repository.*
