import os
from dotenv import load_dotenv

import discord
from discord.ext import commands
from discord import Member
from discord.ext.commands import has_permissions, has_any_role


load_dotenv()
TOKEN = os.getenv('THREDDER_TOKEN')
intents = discord.Intents.default()
intents.members = True
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix="<>", help_command=None, intents=intents)
tracking_channels = {}
exclude_users = set()
track_replies = {}

@bot.event
async def on_ready():
    servers = list(bot.guilds)
    print('We have logged in as {0.user}'.format(bot))
    print('\n'.join(guild.name for guild in servers))

@bot.command(name="track", pass_context=True)
@has_permissions(manage_messages=True)
async def track(ctx, channel_id):
    flag = 0
    for channel in ctx.message.guild.channels:
        if str(channel.id) == channel_id:
            flag = 1
            tracking_channels.setdefault(str(ctx.message.guild).lower(),[]).append(channel.id)
    if(flag):
        await ctx.message.channel.send(f"{channel_id} channel now tracking!")
    else:
        await ctx.message.channel.send(f"{channel_id} channel doesn't exist!")

@bot.command(name="get_id", pass_context=True)
async def get_id(ctx):
    await ctx.message.channel.send(ctx.message.channel.id)

@bot.command(name="stop", pass_context=True)
@has_permissions(manage_messages=True)
async def stop(ctx, arg):
    if str(ctx.message.guild).lower() in tracking_channels and int(arg) in tracking_channels[str(ctx.message.guild).lower()]:
        tracking_channels[str(ctx.message.guild).lower()] = [val for val in tracking_channels[str(ctx.message.guild).lower()] if val != int(arg)]
        await ctx.message.channel.send(f"Stopped Tracking {arg} channel!")
    else:
        await ctx.message.channel.send("Error!")

@bot.command(name="exclude", pass_context=True)
@has_permissions(manage_messages=True)
async def exclude(ctx, arg):
    exclude_users.add(arg)
    print(exclude_users)
    await ctx.message.channel.send(f"User with ID {arg} excluded!")

@bot.command(name="include", pass_context=True)
@has_permissions(manage_messages=True)
async def include(ctx, arg):
    if arg in exclude_users:
        exclude_users.remove(arg)
        await ctx.message.channel.send(f"User {arg} now tracked again!")
    else:
        await ctx.message.channel.send(f"User {arg} was never untracked!")

@bot.command(name="close", pass_context=True)
@has_permissions(manage_messages=True, manage_threads=True)
async def close(ctx):
    await ctx.channel.edit(name='[closed]' + ctx.channel.name)

@bot.command(name="solve", pass_context=True)
@has_permissions(manage_messages=True, manage_threads=True)
async def solve(ctx):
    await ctx.channel.edit(name='[solved]' + ctx.channel.name, archived=True)


@bot.command(name="help", pass_context=True)
@has_permissions(manage_messages=True)
async def help(ctx):
    await ctx.message.channel.send(f"1. `<>exclude user_id`: Won't Create threads for this user.\n2. `<>include user_id`: Track an excluded user again\n3. `<>track channel_id`: This channel is tracked to create threads\n4. `<>stop channel_id`: This channel is stopped tracking\n5. `<>get_id`: Used to get id of current channel\n6. `<>close`: Close current thread (does not archive)\n7. `<>solve`: Solve current thread (archives the thread)\n8. `<>add_reply prompt, reply`: Sends the `reply` when `prompt` is present in a message\n9. `<>remove_reply prompt`: Removes the reply for `prompt`\n10. `<>list_replies`: Lists all the replies")

@bot.command(name="add_reply", pass_context=True)
@has_any_role("Terminator","Skynet")
async def add_reply(ctx, *, message):
    msg = message.split(",")
    if bot.command_prefix in message:
        await ctx.message.channel.send(f"Can't have {bot.command_prefix} in message, dum dum!")
    else:
        track_replies.setdefault(str(ctx.message.guild).lower(),{})[(msg[0]).lower()] = msg[1]
        await ctx.message.channel.send(f"'{msg[1]}' will be replied when '{msg[0]}' is mentioned!")

@add_reply.error
async def add_reply(ctx, error):
    if isinstance(error, commands.MissingAnyRole):
        text = "Sorry {}, you do not have the required role to do that!".format(ctx.message.author)
        await ctx.message.channel.send(text)
    elif isinstance(error, commands.MissingRequiredArgument):
        text = f"Missing a required argument: {error.param}"
        await ctx.message.channel.send(text)

@bot.command(name="remove_reply", pass_context=True)
@has_any_role("Terminator","Skynet")
async def remove_reply(ctx, *, message):
    if bot.command_prefix in message:
        await ctx.message.channel.send(f"Can't have {bot.command_prefix} in message, dum dum!")
    else:
        if (message).lower() in track_replies[str(ctx.message.guild).lower()]:
            del track_replies[str(ctx.message.guild).lower()][(message).lower()]
            await ctx.message.channel.send(f"'{message}' no longer tracked!")
        else:
            await ctx.message.channel.send("That keyword was never tracked in the first place, dum dum!")

@remove_reply.error
async def remove_reply(ctx, error):
    if isinstance(error, commands.MissingAnyRole):
        text = "Sorry {}, you do not have the required role to do that!".format(ctx.message.author)
        await ctx.message.channel.send(text)
    elif isinstance(error, commands.MissingRequiredArgument):
        text = f"Missing a required argument: {error.param}"
        await ctx.message.channel.send(text)

@bot.command(name="list_replies", pass_context=True)
@has_any_role("Terminator","Skynet")
async def list_replies(ctx):
    if len(track_replies[str(ctx.message.guild).lower()]) == 0:
        await ctx.message.channel.send("There are no keywords currently being tracked!")
    else:
        await ctx.message.channel.send("Here are the keywords currently being tracked:")
        await ctx.message.channel.send(track_replies[str(ctx.message.guild).lower()])

@list_replies.error
async def list_replies(ctx, error):
    if isinstance(error, commands.MissingAnyRole):
        text = "Sorry {}, you do not have the required role to do that!".format(ctx.message.author)
        await ctx.message.channel.send(text)
    elif isinstance(error, commands.MissingRequiredArgument):
        text = f"Missing a required argument: {error.param}"
        await ctx.message.channel.send(text)

@track.error
async def add_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        text = "Sorry {}, you do not have permissions to do that!".format(ctx.message.author)
        await ctx.message.channel.send(text)
    elif isinstance(error, commands.MissingRequiredArgument):
        text = f"Missing a required argument: {error.param}"
        await ctx.message.channel.send(text)

@stop.error
async def remove_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        text = "Sorry {}, you do not have permissions to do that!".format(ctx.message.author)
        await ctx.message.channel.send(text)
    elif isinstance(error, commands.MissingRequiredArgument):
        text = f"Missing a required argument: {error.param}"
        await ctx.message.channel.send(text)

@exclude.error
async def exclude_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        text = "Sorry {}, you do not have permissions to do that!".format(ctx.message.author)
        await ctx.message.channel.send(text)
    elif isinstance(error, commands.MissingRequiredArgument):
        text = f"Missing a required argument: {error.param}"
        await ctx.message.channel.send(text)

@include.error
async def include_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        text = "Sorry {}, you do not have permissions to do that!".format(ctx.message.author)
        await ctx.message.channel.send(text)
    elif isinstance(error, commands.MissingRequiredArgument):
        text = f"Missing a required argument: {error.param}"
        await ctx.message.channel.send(text)

@close.error
async def close_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        text = "Sorry {}, you do not have permissions to do that!".format(ctx.message.author)
        await ctx.message.channel.send(text)
    elif isinstance(error, commands.MissingRequiredArgument):
        text = f"Missing a required argument: {error.param}"
        await ctx.message.channel.send(text)

@solve.error
async def solve_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        text = "Sorry {}, you do not have permissions to do that!".format(ctx.message.author)
        await ctx.message.channel.send(text)
    elif isinstance(error, commands.MissingRequiredArgument):
        text = f"Missing a required argument: {error.param}"
        await ctx.message.channel.send(text)

@bot.event
async def on_message(message):
    if str(message.author.id) not in exclude_users:
        if  bot.command_prefix not in message.content and str(message.guild).lower() in tracking_channels and message.channel.id in tracking_channels[str(message.guild).lower()]:
            name = ' '.join(message.content.partition('issue:')[2].split()[:5])
            await message.create_thread(
                name=name,
                auto_archive_duration=1440,
            )
        if str(message.guild).lower() in track_replies and message.author != bot.user and bot.command_prefix not in message.content:
            triggers = [x for x in message.content.lower().split() if x in track_replies[str(message.guild).lower()]]
            for trigger in triggers:
                await message.channel.send(track_replies[str(message.guild).lower()][trigger])
        else:
            await bot.process_commands(message)
    else:
        await bot.process_commands(message)

bot.run(TOKEN)


