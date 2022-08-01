from constants_imports_utils import *

# WIP, VERY OBVIOUSLY NOT COMPLETE.
# TODO: Catch all possible error types over time and handle them so the bot doesn't straight up die.
# TODO: There are also sections containing repeated code. KIV for truncation opportunities.

meetups = bot.create_group("meetups", "Handle meetups!")

class MeetupView(discord.ui.View):
    # A subclass of Pycord's View that includes buttons to interact with meetups.
    
    # "Join meetup" button
    @discord.ui.button(label = "Join this meetup", style = discord.ButtonStyle.green)
    async def join_button_callback(self, button, interaction):
        ctx = await bot.get_application_context(interaction)
        try:
            msg_meetup_id = re.search("(\(Meetup ID: )(\w+)(\))", interaction.message.embeds[0].footer.text).group(2)
        except TypeError as err:
            print("Oops! Error!")
            return None
        else:
            await ctx.invoke(join_meetup, meetup_id = msg_meetup_id)

    # "Leave meetup" button
    @discord.ui.button(label = "Leave this meetup", style = discord.ButtonStyle.red)
    async def leave_button_callback(self, button, interaction):
        ctx = await bot.get_application_context(interaction)
        try:
            msg_meetup_id = re.search("(\(Meetup ID: )(\w+)(\))", interaction.message.embeds[0].footer.text).group(2)
        except TypeError as err:
            print("Oops! Error!")
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
                        participants_ser: str):
    
    # Helper function that creates the meetup embed.
    # This is so I don't have to write the same code over and over again.
    meetup_embed = discord.Embed(
                                    color = MEETUPS_CFG["embed_color"],
                                    title = "proposes a meetup!",
                                    description = f"{meetup_desc}"
                                    )
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
    
    guild, guild_channel_list = await init_guild_variables()
    bot_db, cur = get_db()

    for row in bot_db.execute("SELECT * FROM meetups").fetchall():
        meetup_id, author_mention, meetup_msg_id, meetup_desc, meetup_time, meetup_location, participants_ser = row

        meetup_author = discord.utils.get(guild.members, mention = author_mention)
        meetup_embed = construct_meetup_embed(meetup_author, meetup_id, meetup_desc, meetup_time, meetup_location, participants_ser)    
        meetups_channel = discord.utils.get(guild_channel_list, name = MEETUPS_CFG["meetups_channel"])
        meetup_msg = await meetups_channel.fetch_message(meetup_msg_id)
        await meetup_msg.edit(embed = meetup_embed, view = MeetupView())

@meetups.command(description = "Add a new meetup!")
async def add_meetup(ctx: discord.ApplicationContext, \
                        meetup_id: discord.Option(str, "Name your meetup!"), \
                        meetup_desc: discord.Option(str, "Describe your meetup!"), \
                        meetup_time: discord.Option(str, "Set a time! (WIP: there are no input restrictions for now.)"), \
                        meetup_location: discord.Option(str, "Where shall we all meet?")):

    guild, guild_channel_list = await init_guild_variables()
    bot_db, cur = get_db()
    

    # Ensure our meetup_id is unique in the database since we are using it as our primary key.
    # Also, that it is alphanumeric and it is not longer than 16 characters.
    if not meetup_id.isalpha():
        await ctx.send_response("Not a valid ID! (Please use only numbers and letters for your ID!)")
        return 
    elif len(meetup_id) > 16:
        await ctx.send_response("Not a valid ID! (Please make your ID between 8 and 16 characters long!)")
        return 
    elif len(cur.execute("SELECT * FROM meetups WHERE id = ?", (meetup_id,)).fetchall()):
        await ctx.send_response("There is already a meetup with this name! Choose another name please!", ephemeral = True)
        return
    
    # Our participants list will basically be a collection of the names of individuals attending the meetup.
    participants = [ctx.author.mention]
    # Participants, SERialized.
    participants_ser = json.dumps(participants)

    meetup_embed = construct_meetup_embed(ctx.author, meetup_id, meetup_desc, meetup_time, meetup_location, participants_ser)
    meetups_channel = discord.utils.get(guild_channel_list, name = MEETUPS_CFG["meetups_channel"])
    meetup_msg = await meetups_channel.send(embed = meetup_embed, view = MeetupView())
    
    cur.execute("INSERT INTO meetups (id, meetup_owner, message_id, meetup_desc, meetup_time, meetup_location, participants) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (meetup_id, ctx.author.mention, meetup_msg.id, meetup_desc, meetup_time, meetup_location, participants_ser))
    bot_db.commit()
    bot_db.close()
    await ctx.send_response(f"Meetup created! Check <#{meetups_channel.id}> for the meetup!", ephemeral = True)

@meetups.command(description = "Edit an existing meetup.")
async def edit_meetup(ctx, meetup_id: discord.Option(str), \
                        meetup_desc: discord.Option(str, "Enter a new description!", required = False, default = ''), \
                        meetup_time: discord.Option(str, "Enter a new time! (WIP: there are no input restrictions for now.)", required = False, default = ''), \
                        meetup_location: discord.Option(str, "Enter a new location!", required = False, default = '')):

    guild, guild_channel_list = await init_guild_variables()
    bot_db, cur = get_db()

    try:
        _, author_mention, meetup_msg_id, old_meetup_desc, old_meetup_time, old_meetup_location, participants_ser = cur.execute("SELECT * FROM meetups WHERE id = ?", (meetup_id,)).fetchone()
    except (sqlite3.Error, TypeError) as err:
        await ctx.send_response("This meetup doesn't exist :(", ephemeral = True)
        return None
        
    if ctx.author.mention != author_mention:
        await ctx.send_response("You don't have perms to edit this message (ownership transfers coming soon). Please ask the person who created this meetup to edit it!", ephemeral = True)
        return None
    
    new_meetup_desc = meetup_desc if len(meetup_desc) else old_meetup_desc
    new_meetup_time = meetup_time if len(meetup_time) else old_meetup_time
    new_meetup_location = meetup_location if len(meetup_location) else old_meetup_location

    meetup_embed = construct_meetup_embed(ctx.author, meetup_id, new_meetup_desc, new_meetup_time, new_meetup_location, participants_ser)    
    meetups_channel = discord.utils.get(guild_channel_list, name = MEETUPS_CFG["meetups_channel"])
    meetup_msg = await meetups_channel.fetch_message(meetup_msg_id)
    
    await meetup_msg.edit(embed = meetup_embed, view = MeetupView())
    
    cur.execute(f"UPDATE meetups SET message_id = ?, meetup_desc = ?, meetup_time = ?, meetup_location = ? WHERE id = ?",
        (meetup_msg_id, new_meetup_desc, new_meetup_time, new_meetup_location, meetup_id))

    bot_db.commit()
    bot_db.close()

    await ctx.send_response("Meetup updated!", ephemeral = True)

@meetups.command(description = "See the available meetups!")
async def list_meetups(ctx):
    await ctx.send_response("Hi, this feature hasn't been implemented yet because I couldn't decide whether this'd be useful or not. The command still exists only because Discord is painfully slow to register/deregister new SlashCommands.", ephemeral = True)


@meetups.command(description = "Join an available meetup!")
async def join_meetup(ctx, meetup_id = discord.Option(str)):
    
    guild, guild_channel_list = await init_guild_variables()
    bot_db, cur = get_db()

    try:
        _, author, meetup_msg_id, meetup_desc, meetup_time, meetup_location, participants_ser = cur.execute("SELECT * FROM meetups WHERE id = ?", (meetup_id,)).fetchone()
    except (sqlite3.Error, TypeError) as err:
        await ctx.send_response("This meetup doesn't exist :(", ephemeral = True)
        return None
    
    participants = json.loads(participants_ser)
    if ctx.author.mention in participants:
        await ctx.send_response("You already joined this meetup! Maybe you wanted to join another one instead? :O", ephemeral = True)
        return None
    else:
        participants.append(ctx.author.mention)
        participants_ser = json.dumps(participants)

        # Find the owner of this meetup.
        author = discord.utils.get(guild.members, mention = author)
        cur.execute(f"UPDATE meetups SET participants = ? WHERE id = ?", (participants_ser, meetup_id))

        meetup_embed = construct_meetup_embed(author, meetup_id, meetup_desc, meetup_time, meetup_location, participants_ser)    
        meetups_channel = discord.utils.get(guild_channel_list, name = MEETUPS_CFG["meetups_channel"])
        meetup_msg = await meetups_channel.fetch_message(meetup_msg_id)
        
        await meetup_msg.edit(embed = meetup_embed, view = MeetupView())

        bot_db.commit()
        bot_db.close()
        await ctx.send_response("Done! Welcome aboard!", ephemeral = True)

@meetups.command(description = "Leave a meetup you're in!")
async def leave_meetup(ctx, meetup_id = discord.Option(str)):
    guild, guild_channel_list = await init_guild_variables()
    bot_db, cur = get_db()

    try:
        _, author, meetup_msg_id, meetup_desc, meetup_time, meetup_location, participants_ser = cur.execute("SELECT * FROM meetups WHERE id = ?", (meetup_id,)).fetchone()
    except (sqlite3.Error, TypeError) as err:
        await ctx.send_response("This meetup doesn't exist :(", ephemeral = True)
        return None
    
    participants = json.loads(participants_ser)
    if ctx.author.mention not in participants:
        await ctx.send_response("You weren't already in this meetup! sus.", ephemeral = True)
        return None
    else:
        participants.remove(ctx.author.mention)
        participants_ser = json.dumps(participants)

        # Find the owner of this meetup.
        author = discord.utils.get(guild.members, mention = author)
        cur.execute(f"UPDATE meetups SET participants = ? WHERE id = ?", (participants_ser, meetup_id))

        meetup_embed = construct_meetup_embed(author, meetup_id, meetup_desc, meetup_time, meetup_location, participants_ser)    
        meetups_channel = discord.utils.get(guild_channel_list, name = MEETUPS_CFG["meetups_channel"])
        meetup_msg = await meetups_channel.fetch_message(meetup_msg_id)
        
        await meetup_msg.edit(embed = meetup_embed, view = MeetupView())

        bot_db.commit()
        bot_db.close()
        await ctx.send_response("Sorry to see you go :(", ephemeral = True)