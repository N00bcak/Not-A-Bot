from NotABot.common import bot, log, cfg, general_utils, GUILD
from Crypto.Hash import MD5
import discord
import asyncio
import sqlite3
import json
import re
import base64

# TODO: There are also sections containing repeated code. KIV for truncation opportunities.

meetups = bot.create_group(name = "meetups", description = "Handle meetups!")

class MeetupView(discord.ui.View):
    # A subclass of Pycord's View that includes buttons to interact with meetups.
    
    # "Join meetup" button
    @discord.ui.button(label = "Join this meetup", style = discord.ButtonStyle.green, custom_id = 'meetupview:join')
    async def join_button_callback(self, button, interaction):
        ctx = await bot.get_application_context(interaction)
        await ctx.response.defer(invisible = False, ephemeral = True)
        try:
            msg_meetup_id = re.search("(\(Meetup ID: )(\w+)(\))", interaction.message.embeds[0].footer.text).group(2)
        except TypeError as err:
            log.warning(f"Oops! Error: {err}")
            return None
        else:
            await ctx.invoke(join_meetup, meetup_id = msg_meetup_id)

    # "Leave meetup" button
    @discord.ui.button(label = "Leave this meetup", style = discord.ButtonStyle.red, custom_id = 'meetupview:leave')
    async def leave_button_callback(self, button, interaction):
        ctx = await bot.get_application_context(interaction)
        await ctx.response.defer(invisible = False, ephemeral = True)
        try:
            msg_meetup_id = re.search("(\(Meetup ID: )(\w+)(\))", interaction.message.embeds[0].footer.text).group(2)
        except TypeError as err:
            log.warning(f"Oops! Error: {err}")
            return None
        else:
            await ctx.invoke(leave_meetup, meetup_id = msg_meetup_id)

    def __init__(self):
        super().__init__(timeout = None)

def construct_meetup_embed(author: discord.User, \
                        meetup_id: str, \
                        meetup_desc: str, \
                        meetup_time: str, \
                        meetup_location: str, \
                        participants_ser: str,
                        author_name = None,
                        author_avatar = None):
    
    # Helper function that creates the meetup embed.
    # This is so I don't have to write the same code over and over again.
    meetup_embed = discord.Embed(
                                    color = cfg.MEETUPS_CFG["embed_color"],
                                    title = "proposes a meetup!",
                                    description = f"{meetup_desc}"
                                    )
    if author is None:
        meetup_embed.set_author(name = author_name, icon_url = author_avatar)
    else:
        meetup_embed.set_author(name = author, icon_url = author.display_avatar)
    meetup_embed.set_footer(text = f"Join me by typing `/meetup join_meetup` or clicking the buttons below! (Meetup ID: {meetup_id})")

    participants = json.loads(participants_ser)
    meetup_embed.add_field(name = "Participants", value = '\n'.join(participants) if len(participants) else "Not even the host wants to go for their own meetup :(", inline = False)
    meetup_embed.add_field(name = "Time", value = meetup_time)
    meetup_embed.add_field(name = "Location", value = meetup_location)
    
    return meetup_embed

async def refresh_meetups():
    # Improve the bot's resilience against restarts and... bug hunters.
    # But if there is a better way to refresh buttons on messages after resets, you can tell me about it :D
    
    guild, guild_channel_list = await general_utils.init_guild_variables()
    bot_db, cur = general_utils.get_db()

    for row in bot_db.execute("SELECT * FROM meetups").fetchall():
        meetup_id, author_mention, meetup_msg_id, meetup_desc, meetup_time, meetup_location, participants_ser = row
        
        print(f"Refreshing meetup {row}")

        try:
            meetups_channel = discord.utils.get(guild_channel_list, name = cfg.MEETUPS_CFG["meetups_channel"])
            meetup_msg = await meetups_channel.fetch_message(meetup_msg_id)
            meetup_author = discord.utils.get(guild.members, mention = author_mention)

            if meetup_author is None:
                author_proxy = meetup_msg.embeds[0].author
                # Retrieve the author from the previous embed.
                meetup_embed = construct_meetup_embed(None, meetup_id, meetup_desc, meetup_time, meetup_location, participants_ser, 
                                author_name = author.name, author_avatar = author.icon_url)   
            else:
                meetup_embed = construct_meetup_embed(meetup_author, meetup_id, meetup_desc, meetup_time, meetup_location, participants_ser)    
            await meetup_msg.edit(embed = meetup_embed, view = MeetupView())
        except discord.errors.NotFound as e:
            log.warning(e)
            continue

@meetups.command(description = "Add a new meetup!")
async def add_meetup(ctx: discord.ApplicationContext, \
                        meetup_desc: discord.Option(str, "Describe your meetup!"), \
                        meetup_time: discord.Option(str, "Set a time!"), \
                        meetup_location: discord.Option(str, "Where shall we all meet?")):

    await ctx.response.defer(invisible = False, ephemeral = True)
    log.info(f"{ctx.author.name} is trying to add a meetup!")
    guild, guild_channel_list = await general_utils.init_guild_variables()
    bot_db, cur = general_utils.get_db()
    
    # Our participants list will basically be a collection of the names of individuals attending the meetup.
    participants = [ctx.author.mention]
    # Participants, SERialized.
    participants_ser = json.dumps(participants)

    # Generate a random meetup id that is distinct from all existing meetup IDs.
    h = MD5.new()
    trunc_meetup_desc = general_utils.get_alphanumeric_characters(meetup_desc)
    if len(trunc_meetup_desc) > 16:
        orig_meetup_id = trunc_meetup_desc[:16]
    else:
        h.update(f"{meetup_desc}_{meetup_time}".encode())
        orig_meetup_id = h.hexdigest()[:16]

    meetup_id = orig_meetup_id
    i = 0
    # While meetup exists, just increment to get an id. I really don't care enough.
    while len(cur.execute("SELECT * FROM meetups WHERE id = ?", (meetup_id,)).fetchall()):
        i += 1
        meetup_id = f"{orig_meetup_id}_{str(i)}"
    
    meetup_embed = construct_meetup_embed(ctx.author, meetup_id, meetup_desc, meetup_time, meetup_location, participants_ser)
    meetups_channel = discord.utils.get(guild_channel_list, name = cfg.MEETUPS_CFG["meetups_channel"])
    meetup_msg = await meetups_channel.send(embed = meetup_embed, view = MeetupView())
    
    cur.execute("INSERT INTO meetups (id, meetup_owner, message_id, meetup_desc, meetup_time, meetup_location, participants) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (meetup_id, ctx.author.mention, meetup_msg.id, meetup_desc, meetup_time, meetup_location, participants_ser))
    bot_db.commit()
    bot_db.close()
    await ctx.send_followup(f"Meetup created! Check <#{meetups_channel.id}> for the meetup!", ephemeral = True)

@meetups.command(description = "Edit an existing meetup.")
async def edit_meetup(ctx, meetup_id: discord.Option(str), \
                        meetup_desc: discord.Option(str, "Enter a new description!", required = False, default = ''), \
                        meetup_time: discord.Option(str, "Enter a new time! (WIP: there are no input restrictions for now.)", required = False, default = ''), \
                        meetup_location: discord.Option(str, "Enter a new location!", required = False, default = '')):

    await ctx.response.defer(invisible = False, ephemeral = True)
    guild, guild_channel_list = await general_utils.init_guild_variables()
    bot_db, cur = general_utils.get_db()

    try:
        _, author_mention, meetup_msg_id, old_meetup_desc, old_meetup_time, old_meetup_location, participants_ser = cur.execute("SELECT * FROM meetups WHERE id = ?", (meetup_id,)).fetchone()
    except (sqlite3.Error, TypeError) as err:
        await ctx.send_followup("This meetup doesn't exist :(", ephemeral = True)
        return 
    else:
        if ctx.author.mention != author_mention:
            await ctx.send_followup("You don't have perms to edit this message (ownership transfers coming soon). Please ask the person who created this meetup to edit it!", ephemeral = True)
            return 
        
        new_meetup_desc = meetup_desc if len(meetup_desc) else old_meetup_desc
        new_meetup_time = meetup_time if len(meetup_time) else old_meetup_time
        new_meetup_location = meetup_location if len(meetup_location) else old_meetup_location

        meetup_embed = construct_meetup_embed(ctx.author, meetup_id, new_meetup_desc, new_meetup_time, new_meetup_location, participants_ser)    
        meetups_channel = discord.utils.get(guild_channel_list, name = cfg.MEETUPS_CFG["meetups_channel"])
        meetup_msg = await meetups_channel.fetch_message(meetup_msg_id)
        
        await meetup_msg.edit(embed = meetup_embed, view = MeetupView())
        
        cur.execute(f"UPDATE meetups SET message_id = ?, meetup_desc = ?, meetup_time = ?, meetup_location = ? WHERE id = ?",
            (meetup_msg_id, new_meetup_desc, new_meetup_time, new_meetup_location, meetup_id))

        bot_db.commit()
        bot_db.close()

        await ctx.send_response("Meetup updated!", ephemeral = True)

@meetups.command(description = "Join an available meetup!")
async def join_meetup(ctx, meetup_id = discord.Option(str)):
    
    guild, guild_channel_list = await general_utils.init_guild_variables()
    bot_db, cur = general_utils.get_db()

    try:
        _, author, meetup_msg_id, meetup_desc, meetup_time, meetup_location, participants_ser = cur.execute("SELECT * FROM meetups WHERE id = ?", (meetup_id,)).fetchone()
    except (sqlite3.Error, TypeError) as err:
        await ctx.send_followup("This meetup doesn't exist :(", ephemeral = True)
        return 
    
    participants = json.loads(participants_ser)
    if ctx.author.mention in participants:
        await ctx.send_followup("You already joined this meetup! Maybe you wanted to join another one instead? :O", ephemeral = True)
        return 
    else:
        participants.append(ctx.author.mention)
        participants_ser = json.dumps(participants)

        # Find the owner of this meetup.
        author = discord.utils.get(guild.members, mention = author)
        cur.execute(f"UPDATE meetups SET participants = ? WHERE id = ?", (participants_ser, meetup_id))

        meetup_embed = construct_meetup_embed(author, meetup_id, meetup_desc, meetup_time, meetup_location, participants_ser)    
        meetups_channel = discord.utils.get(guild_channel_list, name = cfg.MEETUPS_CFG["meetups_channel"])
        meetup_msg = await meetups_channel.fetch_message(meetup_msg_id)
        
        await meetup_msg.edit(embed = meetup_embed, view = MeetupView())

        bot_db.commit()
        bot_db.close()
        await ctx.send_followup("Done! Welcome aboard!", ephemeral = True)

@meetups.command(description = "Leave a meetup you're in!")
async def leave_meetup(ctx, meetup_id = discord.Option(str)):
    guild, guild_channel_list = await general_utils.init_guild_variables()
    bot_db, cur = general_utils.get_db()

    try:
        _, author, meetup_msg_id, meetup_desc, meetup_time, meetup_location, participants_ser = cur.execute("SELECT * FROM meetups WHERE id = ?", (meetup_id,)).fetchone()
    except (sqlite3.Error, TypeError) as err:
        await ctx.send_followup("This meetup doesn't exist :(", ephemeral = True)
        return
    
    participants = json.loads(participants_ser)
    if ctx.author.mention not in participants:
        await ctx.send_followup("You weren't already in this meetup! sus.", ephemeral = True)
        return
    else:
        participants.remove(ctx.author.mention)
        participants_ser = json.dumps(participants)

        # Find the owner of this meetup.
        author = discord.utils.get(guild.members, mention = author)
        cur.execute(f"UPDATE meetups SET participants = ? WHERE id = ?", (participants_ser, meetup_id))

        meetup_embed = construct_meetup_embed(author, meetup_id, meetup_desc, meetup_time, meetup_location, participants_ser)    
        meetups_channel = discord.utils.get(guild_channel_list, name = cfg.MEETUPS_CFG["meetups_channel"])
        meetup_msg = await meetups_channel.fetch_message(meetup_msg_id)
        
        await meetup_msg.edit(embed = meetup_embed, view = MeetupView())

        bot_db.commit()
        bot_db.close()
        await ctx.send_followup("Sorry to see you go :(", ephemeral = True)