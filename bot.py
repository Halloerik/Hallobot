"""
Created on 01.05.2020

@author: Erik
"""
import pickle
import sys
import traceback
from typing import TypedDict

import discord
import discord.ext.commands as commands
from discord.errors import Forbidden, LoginFailure, NotFound, HTTPException
from discord.ext.commands import has_permissions, MissingPermissions, RoleNotFound
from emoji import is_emoji

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot('$', intents=intents)


class RoleEmoji(TypedDict):
    # emojis can also be the id of the emoji in case it's a custom emoji.
    # Use get_emoji method before use to make sure everything works
    emoji: str | int
    game: str
    role: discord.Role


class EulaEmoji(TypedDict):
    # emojis can also be the id of the emoji in case it's a custom emoji.
    # Use get_emoji method before use to make sure everything works
    emoji: str | int
    message: discord.Message
    role: discord.Role


role_comments: dict[int, discord.Message] = {}  # guild.id: message

# guild.id : [ {emoji: "🧂", game: "league", role: <@68463464>} ]
role_emojis: dict[int, list[RoleEmoji]] = {}

# guild.id: {message:message.id, emoji:"✅", role: <@68463464>}
eula_comments: dict[int, EulaEmoji] = {}

version = "1.2.0"


@bot.event
async def on_ready():
    await load_comments()
    # print("role_comments", type(role_comments), [(type(k), type(v)) for (k, v) in role_comments.items()])
    # print(role_comments, "\n")

    # print("role_emojis", type(role_emojis),
    #      [(type(k), [(type(v["emoji"]), type(v["game"]), type(v["role"])) for v in vs]) for (k, vs) in
    #       role_emojis.items()])
    # print(role_emojis, "\n")

    # print("eula_comments", type(eula_comments),
    #      [(type(k), (type(v["emoji"]), type(v["message"]), type(v["role"]))) for (k, v) in eula_comments.items()])
    # print(eula_comments, "\n")

    print(f'We have logged in as {bot.user} on {len(bot.guilds)} servers!')


@bot.command(name="hello", pass_context=True)
async def hello(ctx):
    await ctx.channel.send('Hello!')


@bot.command(name="hallo", pass_context=True)
async def hallo(ctx):
    await ctx.channel.send('Hallo!')


@bot.command(name="version", pass_context=True)
async def say_version(ctx):
    await ctx.channel.send(f'I am running on version: {version}')


'''
@bot.command(name="logout", pass_context=True)
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
'''

# TODO make command purge everything after the role_comment if its in the same channel
'''
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
        traceback.print_exc()
'''


@bot.command(name="listen", pass_context=True)
@has_permissions(administrator=True)
async def start_listening_for_roles(ctx):
    global role_comments
    if ctx.guild.id not in role_comments.keys():
        command_parts = ctx.message.content.split(" ")
        if len(command_parts) == 1:
            role_comments[ctx.guild.id] = await ctx.channel.send(
                "Ok! Add roles for me to listen to by using $add_role")
            role_emojis[ctx.guild.id] = []
            save_comments()
        else:
            try:
                message = await ctx.channel.fetch_message(command_parts[1])
            except NotFound:
                await ctx.channel.send("Could not find this message")
                return
            except HTTPException as error:
                if error.status == 400:
                    await ctx.channel.send(f"'{command_parts[1]}' is not a valid message id")
                raise error
            role_comments[ctx.guild.id] = message
            role_emojis[ctx.guild.id] = []
            await ctx.channel.send(
                "Ok! Will listen to that message. Add roles for me to listen to by using $add_role")
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
            except Exception as e:
                print("Error in add role:", type(e))
                traceback.print_exc()
            return

    await ctx.channel.send("You are using this command wrong. $add_role roleName rolePing emoji\n\
    roleName = Name of the Role/Game\n\
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
    roleName = Name of the Role/Game\n\
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


@bot.command(name="list_roles")
@has_permissions(administrator=True)
async def list_roles(ctx: commands.context.Context):
    guild_id = ctx.guild.id
    if guild_id in role_comments.keys():
        await ctx.channel.send(role_comments[guild_id])
        await ctx.channel.send(role_emojis[guild_id])
        await ctx.channel.send(eula_comments[guild_id])
    else:
        await ctx.channel.send("I'm not listening to reactions yet. Try typing '$listen' first")


@list_roles.error
async def add_role_error(ctx, error):
    if isinstance(error, MissingPermissions):
        await ctx.channel.send("You aren't an admin. Cringe :sick:")


@bot.command(name="listen_eula", pass_context=True)
@has_permissions(administrator=True)
async def start_listening_for_eula(ctx):
    global eula_comments
    if ctx.guild.id not in eula_comments.keys():
        command_parts = ctx.message.content.split(" ")
        if len(command_parts) == 4:
            try:
                message = await ctx.channel.fetch_message(command_parts[1])
            except NotFound:
                await ctx.channel.send("Could not find this message")
                return
            except HTTPException as error:
                if error.status == 400:
                    await ctx.channel.send(f"'{command_parts[1]}' is not a valid message id")
                raise error

            role = await commands.RoleConverter().convert(ctx, command_parts[2])

            try:
                emoji = await commands.PartialEmojiConverter().convert(ctx, command_parts[3])
                emoji = emoji.id
            except commands.PartialEmojiConversionFailure:
                emoji = command_parts[3]

            new_eula = {"message": message, "role": role, "emoji": emoji}
            eula_comments[ctx.guild.id] = new_eula

            try:
                save_comments()
                emoji_ = await get_emoji(ctx.guild, emoji)
                await message.add_reaction(emoji_)

            except discord.NotFound:
                await ctx.channel.send("The Comment I was listening too was deleted. I'm going to stop listening here.")
                await stop_listening_for_roles(ctx)
            except TypeError:
                print(message)
                print(role)
                print(emoji)
                traceback.print_exc()
                eula_comments.pop(ctx.guild.id)
                save_comments()
            except Exception as e:
                print("Error in start listening for eula:", type(e))
                traceback.print_exc()
            return

        await ctx.channel.send("You are using this command wrong. $listen_eula messageID rolePing emoji\n\
        messageID = ID of the Eula message\n\
        rolePing = ping the role for that game\n\
        emoji=emoji that's used for confirmation")
        return
    else:
        await ctx.channel.send("I'm already listening to a comment on this Server.")


@start_listening_for_eula.error
async def start_listening_for_eula_error(ctx, error):
    if isinstance(error, MissingPermissions):
        await ctx.channel.send("You aren't an admin. Cringe :sick:")
    elif isinstance(error, Forbidden):
        await ctx.channel.send("Something went wrong. I was not allowed to do that. Please check my permissions")
    else:
        traceback.print_exc()


@bot.command(name="stop_listen_eula", pass_context=True)
@has_permissions(administrator=True)
async def stop_listening_for_eula(ctx):
    global eula_comments
    if ctx.guild.id in eula_comments.keys():
        eula_comment = eula_comments.pop(ctx.guild.id)
        await ctx.channel.send("Ok! I won't listen here anymore")
        message = eula_comment["message"]
        emoji = eula_comment["emoji"]
        try:
            await message.clear_reaction(await get_emoji(ctx.guild, emoji))
        except NotFound:
            pass

        save_comments()
    else:
        await ctx.channel.send("I wasn't listening here anyway.")


@stop_listening_for_eula.error
async def stop_listening_for_eula_error(ctx, error):
    if isinstance(error, MissingPermissions):
        await ctx.channel.send("You aren't an admin. Cringe :sick:")
    elif isinstance(error, Forbidden):
        await ctx.channel.send("Something went wrong. I was not allowed to do that. Please check my permissions")
    else:
        traceback.print_exc()


@bot.event
async def on_raw_reaction_add(reaction_event: discord.RawReactionActionEvent):
    global role_comments
    global eula_comments

    role_comment_emoji = [comment for comment in role_comments.values() if
                          comment.id == reaction_event.message_id]

    if role_comment_emoji:
        role_comment = role_comments[reaction_event.guild_id]
        role_emoji_list = role_emojis[reaction_event.guild_id]
        # user: discord.Member = await role_comment.guild.fetch_member(reaction_event.user_id)
        user: discord.Member = reaction_event.member

        if user == bot.user:
            # print("i reacted myself")
            return
        for d in role_emoji_list:
            # print(type(reaction_event.emoji), reaction_event.emoji)
            if reaction_event.emoji.name == d["emoji"] or reaction_event.emoji.id == d["emoji"]:
                await user.add_roles(d["role"])
                return
        await role_comment.remove_reaction(reaction_event.emoji, user)  # remove an untracked emoji
    elif reaction_event.guild_id in eula_comments.keys():
        eula_comment = eula_comments[reaction_event.guild_id]

        user: discord.Member = reaction_event.member

        if user == bot.user:
            # print("i reacted myself")
            return
        if reaction_event.emoji.name == eula_comment["emoji"] or reaction_event.emoji.id == eula_comment["emoji"]:
            await user.add_roles(eula_comment["role"])
        await eula_comment["message"].remove_reaction(reaction_event.emoji, user)
    else:
        # print("a random comment got reacted on")
        return


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
    cleaned_role_emojis = {guild_id: [{"game": emoji_dict["game"],
                                       "role": emoji_dict["role"].id,
                                       "emoji": emoji_dict["emoji"]}
                                      for emoji_dict in emoji_list
                                      ]
                           for guild_id, emoji_list in role_emojis.items()}
    cleaned_eula_comments = {guild_id: {"message": (eula["message"].channel.id, eula["message"].id),
                                        "role": eula["role"].id,
                                        "emoji": eula["emoji"]}
                             for guild_id, eula in eula_comments.items()}
    # print(cleaned_role_comments)
    # print(cleaned_role_emojis)
    pickle.dump((cleaned_role_comments, cleaned_role_emojis, cleaned_eula_comments), open("role_comments", "wb"))


async def load_comments():
    global role_comments
    global role_emojis
    global eula_comments
    try:
        loaded_stuff = pickle.load(open("role_comments", "rb"))
        if len(loaded_stuff) == 2:
            role_comments, role_emojis = loaded_stuff
        elif len(loaded_stuff) == 3:
            role_comments, role_emojis, eula_comments = loaded_stuff
        # print(f"loading {role_comments}")
        # print(f"loading {role_emojis}")
        mark_for_deletion = set()
        for guild_id, message_tuple in role_comments.items():
            try:
                channel = await bot.fetch_channel(message_tuple[0])
                message = await channel.fetch_message(message_tuple[1])
                role_comments[guild_id] = message
            except discord.NotFound:
                mark_for_deletion.add(guild_id)
        for guild_id, emoji_list in role_emojis.items():
            try:
                guild = await bot.fetch_guild(guild_id)
                for emoji_dict in emoji_list:
                    emoji_dict["role"] = guild.get_role(emoji_dict["role"])
            except discord.NotFound:
                mark_for_deletion.add(guild_id)

        for deletion in mark_for_deletion:
            role_comments.pop(deletion, None)
            role_emojis.pop(deletion, None)

        mark_for_deletion_eula = set()
        for guild_id, eula in eula_comments.items():
            try:
                channel = await bot.fetch_channel(eula["message"][0])
                message = await channel.fetch_message(eula["message"][1])
                eula["message"] = message

                guild = await bot.fetch_guild(guild_id)
                eula["role"] = guild.get_role(eula["role"])

                eula_comments[guild_id] = eula

            except discord.NotFound:
                mark_for_deletion_eula.add(guild_id)

        for deletion in mark_for_deletion_eula:
            eula_comments.pop(deletion, None)

        if mark_for_deletion or mark_for_deletion_eula:
            save_comments()

    except FileNotFoundError:
        save_comments()


async def get_emoji(guild: discord.Guild, emoji: str | int) -> str | discord.Emoji:
    if is_emoji(emoji):
        return emoji
    else:
        emoji = await guild.fetch_emoji(emoji)
        return emoji


if __name__ == '__main__':
    if len(sys.argv) == 1:
        try:
            bot.run(sys.stdin.read())
        except LoginFailure as e:
            print("Invalid Token")
    elif len(sys.argv) != 2:
        print("The bot needs a discord token as argument.")
    else:
        try:
            bot.run(sys.argv[1])
        except LoginFailure as e:
            print("Invalid Token")
