"""
Created on 01.05.2020

@author: Erik
"""
import pickle
import sys
import traceback

import discord
import discord.ext.commands as commands
from discord.errors import Forbidden, LoginFailure, InvalidArgument
from discord.ext.commands import has_permissions, MissingPermissions, RoleNotFound
from emoji import UNICODE_EMOJI

bot = commands.Bot('$')

role_comments = {}  # guild.id: message
role_emojis = {}  # guild.id : [ {emoji: ":salt:", game: league, role: <@68463464>} ]


@bot.event
async def on_ready():
    await load_comments()
    print(f'We have logged in as {bot.user} on {len(bot.guilds)} servers!')


@bot.command(name="hello", pass_context=True)
async def hello(ctx):
    await ctx.channel.send('Hello!')


'''@bot.command(name="logout", pass_context=True)
@has_permissions(administrator=True)
async def logout(ctx):
    """Shuts the bot down"""
    await ctx.channel.send('Good bye!')
    await bot.close()


@logout.error
async def logout_error(ctx, error):
    if isinstance(error, MissingPermissions):
        await ctx.channel.send("You aren't an admin. Cringe :sick:")
    else:
        traceback.print_exc()

@bot.command(name="purge", pass_context=True)
@has_permissions(administrator=True)
async def purge(ctx):
    """Shuts the bot down"""
    await ctx.channel.purge()

@purge.error
async def purge_error(ctx, error):
    if isinstance(error, MissingPermissions):
        await ctx.channel.send("You aren't an admin. Cringe :sick:")
    else:
        traceback.print_exc()'''


@bot.command(name="listen", pass_context=True)
@has_permissions(administrator=True)
async def start_listening_for_roles(ctx):
    global role_comments
    if ctx.guild.id not in role_comments.keys():
        role_comments[ctx.guild.id] = await ctx.channel.send(
            "Ok! Add roles for me to listen to by using $add_role")
        role_emojis[ctx.guild.id] = []
        save_comments()
    else:
        await ctx.channel.send("I'm already listening to a comment on this Server.")


@start_listening_for_roles.error
async def start_listening_for_roles_error(ctx, error):
    if isinstance(error, MissingPermissions):
        await ctx.channel.send("You aren't an admin. Cringe :sick:")
    elif isinstance(error, Forbidden):
        await ctx.channel.send("Something went wrong. I was not allowed to do that. Please check my permissions")
    else:
        traceback.print_exc()


@bot.command(name="stop_listen", pass_context=True)
@has_permissions(administrator=True)
async def stop_listening_for_roles(ctx):
    global role_comments
    if ctx.guild.id in role_comments.keys():
        role_comments.pop(ctx.guild.id, None)
        role_emojis.pop(ctx.guild.id, None)

        await ctx.channel.send("Ok! I won't listen here anymore")
        save_comments()
    else:
        await ctx.channel.send("I wasn't listening here anyway.")


@stop_listening_for_roles.error
async def stop_listening_for_roles_error(ctx, error):
    if isinstance(error, MissingPermissions):
        await ctx.channel.send("You aren't an admin. Cringe :sick:")
    elif isinstance(error, Forbidden):
        await ctx.channel.send("Something went wrong. I was not allowed to do that. Please check my permissions")
    else:
        traceback.print_exc()


@bot.command(name="add_role", pass_context=True)
@has_permissions(administrator=True)
async def add_role(ctx: commands.context.Context):
    # if role_comment is None:
    #    await ctx.channel.send("I'm not listening to reactions yet. Try typing '$listen' first")
    #    return
    if ctx.guild.id not in role_comments.keys():
        await ctx.channel.send("I'm not listening to reactions yet. Try typing '$listen' first")
        return
    else:
        role_comment = role_comments[ctx.guild.id]
        role_emoji_list = role_emojis[ctx.guild.id]

        command_parts = ctx.message.content.split(" ")
        if len(command_parts) == 4:
            game = command_parts[1]
            role = await commands.RoleConverter().convert(ctx, command_parts[2])
            try:
                emoji = await commands.PartialEmojiConverter().convert(ctx, command_parts[3])
                emoji = emoji.id
            except commands.PartialEmojiConversionFailure:
                emoji = command_parts[3]

            if game in [d["game"] for d in role_emoji_list]:
                await ctx.send("This game is already used!")
                return
            if role in [d["role"] for d in role_emoji_list]:
                await ctx.send("This role is already used!")
                return
            if emoji in [d["emoji"] for d in role_emoji_list]:
                await ctx.send("This emoji is already used!")
                return

            new_emoji = {"game": game, "role": role, "emoji": emoji}
            role_emoji_list.append(new_emoji)
            try:
                save_comments()
                text = "Click an Emote to get notified when someone wants to play the corresponding game\n\n"
                for d in role_emoji_list:
                    emoji_ = await get_emoji(ctx.guild, d['emoji'])
                    text += f"{emoji_} → {d['game']}\n"
                    await role_comment.add_reaction(emoji_)
                await role_comment.edit(content=text)

            except discord.NotFound:
                await ctx.channel.send("The Comment I was listening too was deleted. I'm going to stop listening here.")
                await stop_listening_for_roles(ctx)
            except TypeError:
                print(game)
                print(role)
                print(emoji)
                traceback.print_exc()
                role_emoji_list.remove(new_emoji)
                save_comments()
            except InvalidArgument:
                print(game)
                print(role)
                print(emoji)
                traceback.print_exc()
                role_emoji_list.remove(new_emoji)
                save_comments()
            return

    await ctx.channel.send("You are using this command wrong. $add_role roleName rolePing emoji\n\
    gameName = Name of the Game\n\
    rolePing = ping the role for that game\n\
    emoji=emoji that's used to subscribe")
    return


@add_role.error
async def add_role_error(ctx, error):
    if isinstance(error, MissingPermissions):
        await ctx.channel.send("You aren't an admin. Cringe :sick:")
    elif isinstance(error, RoleNotFound):
        await ctx.channel.send("That role doesnt exist.")
    elif isinstance(error, Forbidden):
        await ctx.channel.send("Something went wrong. I was not allowed to do that. Please check my permissions")
    else:
        print(type(error))
        traceback.print_exc()


@bot.command(name="remove_role")
@has_permissions(administrator=True)
async def remove_role(ctx: commands.context.Context):
    if ctx.guild.id not in role_comments.keys():
        await ctx.channel.send("I'm not listening to reactions yet. Try typing '$listen' first")
        return
    else:
        role_comment = role_comments[ctx.guild.id]
        role_emoji_list = role_emojis[ctx.guild.id]
        command_parts = ctx.message.content.split(" ")
        if len(command_parts) == 2:
            game = command_parts[1]
            try:
                role = await commands.RoleConverter().convert(ctx, command_parts[1])
            except commands.RoleNotFound:
                role = None
            try:
                emoji = await commands.PartialEmojiConverter().convert(ctx, command_parts[1])
                emoji = emoji.id
            except commands.PartialEmojiConversionFailure:
                emoji = command_parts[1]

            # print(f"{game}, {role}, {emoji}")
            # print(role_emoji_list)
            emoji_role = [emoji_role for emoji_role in role_emoji_list if (game in emoji_role.values()
                                                                           or role in emoji_role.values()
                                                                           or emoji in emoji_role.values())]
            if emoji_role:
                try:
                    role_emoji_list.remove(emoji_role[0])
                    await role_comment.clear_reaction(await get_emoji(ctx.guild, emoji_role[0]['emoji']))
                    save_comments()
                    if role_emoji_list:  # if still some emojis left
                        text = "Click an Emote to get notified when someone wants to play the corresponding game\n\n"
                        for d in role_emoji_list:
                            emoji = await get_emoji(ctx.guild, d['emoji'])
                            text += f"{emoji} → {d['game']}\n"
                            await role_comment.add_reaction(emoji)
                        await role_comment.edit(content=text)
                    else:
                        await role_comment.edit(content="No roles left."
                                                        + "Add more roles by using $add_role \n"
                                                        + "or use $stop_listen to stop me from listening")

                except discord.NotFound:
                    await ctx.channel.send(
                        "The Comment I was listening too was deleted. I'm going to stop listening here.")
                    await stop_listening_for_roles(ctx)

                return
    await ctx.channel.send("You are using this command wrong. $remove_role <argument>\n\
    argument is any of the following:\n\
    gameName = Name of the Game\n\
    rolePing = ping the role for that game\n\
    emoji=emoji that's used to subscribe")
    return


@remove_role.error
async def add_role_error(ctx, error):
    if isinstance(error, MissingPermissions):
        await ctx.channel.send("You aren't an admin. Cringe :sick:")
    elif isinstance(error, RoleNotFound):
        await ctx.channel.send("That role doesnt exist.")
    elif isinstance(error, Forbidden):
        await ctx.channel.send("Something went wrong. I was not allowed to do that. Please check my permissions")
    else:
        traceback.print_exc()


@bot.event
async def on_raw_reaction_add(reaction_event: discord.RawReactionActionEvent):
    global role_comments

    role_comment_emoji = [comment for comment in role_comments.values() if
                          comment.id == reaction_event.message_id]
    if not role_comment_emoji:
        # print("a random comment got reacted on")
        return
    else:
        role_comment = role_comments[reaction_event.guild_id]
        role_emoji_list = role_emojis[reaction_event.guild_id]
        user: discord.Member = await role_comment.guild.fetch_member(reaction_event.user_id)

        if user == bot.user:
            # print("i reacted myself")
            return
        for d in role_emoji_list:
            # print(type(reaction_event.emoji), reaction_event.emoji)
            if reaction_event.emoji.name == d["emoji"] or reaction_event.emoji.id == d["emoji"]:
                await user.add_roles(d["role"])
                return
        await role_comment.remove_reaction(reaction_event.emoji, user)  # remove an untracked emoji


@bot.event
async def on_raw_reaction_remove(reaction_event: discord.RawReactionActionEvent):
    global role_comments
    role_comment_emoji = [comment for comment in role_comments.values() if
                          comment.id == reaction_event.message_id]
    if not role_comment_emoji:
        # print("a random comment got reacted on")
        return
    else:
        role_comment = role_comments[reaction_event.guild_id]
        role_emoji_list = role_emojis[reaction_event.guild_id]
        user: discord.Member = await role_comment.guild.fetch_member(reaction_event.user_id)

        if user == bot.user:
            # print("i reacted myself")
            return
        for d in role_emoji_list:
            # print(type(reaction_event.emoji), reaction_event.emoji)
            if reaction_event.emoji.name == d["emoji"] or reaction_event.emoji.id == d["emoji"]:
                await user.remove_roles(d["role"])
                return


# Welcome DM function
"""
@client.event
async def on_member_join(member):
    await member.create_dm()
    await member.dm_channel.send(
        f'''Hey schön dass du da bist! :flag_de: 
Niemand mag Regeln, aber was wir noch weniger mögen sind:
Rassismus, Homophobie, Chauvinismus und andere "-ismen". 
Auch Belästigung der anderen Mitglieder wird nicht toleriert. 
*>> Sei kein Arschloch.*

Darüberhinaus fühl dich wie Zuhause und sei willkommen! 
-------------------------------------------------------
Hey Nice of you to join our Server! :flag_gb: 
Nobody likes rules but what we like less is:
Racism, Homophobia, Chauvinism, other -isms and harassment of users. 
*>> Don't be an asshole.*

Other than that feel free and welcome to express yourself.''')
"""


def save_comments():
    # print(role_comments)
    # print(role_emojis)

    cleaned_role_comments = {guild_id: (message.channel.id, message.id) for guild_id, message in role_comments.items()}
    cleaned_role_emojis = {guild_id: [
        {"game": emoji_dict["game"], "role": emoji_dict["role"].id, "emoji": emoji_dict["emoji"]}
        for emoji_dict in emoji_list
    ]
        for guild_id, emoji_list in role_emojis.items()}
    # print(cleaned_role_comments)
    # print(cleaned_role_emojis)
    pickle.dump((cleaned_role_comments, cleaned_role_emojis), open("role_comments", "wb"))


async def load_comments():
    global role_comments
    global role_emojis
    try:
        role_comments, role_emojis = pickle.load(open("role_comments", "rb"))
        # print(f"loading {role_comments}")
        # print(f"loading {role_emojis}")
        for guild_id, message_tuple in role_comments.items():
            channel = await bot.fetch_channel(message_tuple[0])
            message = await channel.fetch_message(message_tuple[1])
            role_comments[guild_id] = message

        for guild_id, emoji_list in role_emojis.items():
            guild = await bot.fetch_guild(guild_id)
            for emoji_dict in emoji_list:
                emoji_dict["role"] = guild.get_role(emoji_dict["role"])

        # print(f"loaded {role_comments}")
        # print(f"loaded {role_emojis}")

    except FileNotFoundError:
        save_comments()


async def get_emoji(guild, emoji):
    # print(UNICODE_EMOJI['en'].keys())
    if emoji in UNICODE_EMOJI['en'].keys():
        return emoji
    else:
        emoji = await guild.fetch_emoji(emoji)
        return emoji


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("The bot needs a discord token as argument.")
    else:
        try:
            bot.run(sys.argv[1])
        except LoginFailure as e:
            print("Invalid Token")
