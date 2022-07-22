from constants_imports_utils import *

# WIP, VERY OBVIOUSLY NOT COMPLETE.
# TODO: Catch all possible error types over time and handle them so the bot doesn't straight up die.

meetups = bot.create_group("meetups", "Handle meetups!")

@meetups.command(description = "Add a new meetup!")
async def add_meetup(ctx: discord.ApplicationContext, \
                        meetup_id: discord.Option(str, "Name your meetup!"), \
                        meetup_desc: discord.Option(str, "Describe your meetup"), \
                        meetup_time: discord.Option(str, "Set a time!"), \
                        meetup_location: discord.Option(str, "Where shall your friends meet?")):

    # TODO: Regex the meetup_time so it can be converted easily into a datetime.

    bot_db, cur = get_db()

    # Ensure our meetup_id is unique in the database since we are using it as our primary key.
    if len(cur.execute(f"SELECT * FROM meetups WHERE id='{meetup_id}'").fetchall()):
        await ctx.respond("There is already a meetup with this name! Choose another name please!")
        return None

    
    meetup_embed = discord.Embed(
                                color = MEETUPS_CFG["embed_color"],
                                title = "proposes a meetup!",
                                description = f"{meetup_desc}"
                                )
    meetup_embed.set_author(name = ctx.author, icon_url = ctx.author.display_avatar)
    meetup_embed.set_footer(text = f"(Meetup ID: {meetup_id})")
    meetup_embed.add_field(name = "Time", value = meetup_time)
    meetup_embed.add_field(name = "Location", value = meetup_location)

    meetups_channel = discord.utils.get(bot.get_all_channels(), name = MEETUPS_CFG["meetups_channel"])
    meetup_msg = await meetups_channel.send(embed = meetup_embed)
    
    cur.execute(f""" INSERT INTO meetups (id, message_id, meetup_desc, meetup_time, meetup_location) 
                VALUES ('{meetup_id}', '{meetup_msg.id}' ,'{meetup_desc}', '{meetup_time}', '{meetup_location}')""")
    bot_db.commit()
    bot_db.close()
    await ctx.send(f"Meetup created! Check <#{meetups_channel.id}> for the meetup!")

@meetups.command(description = "Edit an existing meetup.")
async def edit_meetup(ctx, meetup_id: discord.Option(str), \
                        meetup_desc: discord.Option(str, "Enter a new description", required = False, default = ''), \
                        meetup_time: discord.Option(str, "Enter a new time", required = False, default = ''), \
                        meetup_location: discord.Option(str, "Enter a new location", required = False, default = '')):

    bot_db, cur = get_db()

    try:
        meetup_id, meetup_msg_id, old_meetup_desc, old_meetup_time, old_meetup_location, participants = cur.execute(f"SELECT * FROM meetups WHERE id = '{meetup_id}'").fetchone()
    except sqlite3.Error as err:
        await ctx.respond("This meetup doesn't exist :(")
        return None

    new_meetup_desc = meetup_desc if len(meetup_desc) else old_meetup_desc
    new_meetup_time = meetup_time if len(meetup_time) else old_meetup_time
    new_meetup_location = meetup_location if len(meetup_location) else old_meetup_location

    meetup_embed = discord.Embed(
                                color = MEETUPS_CFG["embed_color"],
                                title = "proposes a meetup!",
                                description = f"{new_meetup_desc}\n{participants}"
                                )

    meetup_embed.set_author(name = ctx.author, icon_url = ctx.author.display_avatar)
    meetup_embed.set_footer(text = f"(Meetup ID: {meetup_id})")
    meetup_embed.add_field(name = "Time", value = new_meetup_time)
    meetup_embed.add_field(name = "Location", value = new_meetup_location)
    
    meetups_channel = discord.utils.get(bot.get_all_channels(), name = MEETUPS_CFG["meetups_channel"])
    meetup_msg = await meetups_channel.fetch_message(meetup_msg_id)
    
    await meetup_msg.edit(embed = meetup_embed)
    
    cur.execute(f"UPDATE meetups SET message_id = '{meetup_msg_id}', meetup_desc = '{new_meetup_desc}', meetup_time = '{new_meetup_time}', meetup_location = '{new_meetup_location}' WHERE id = '{meetup_id}'")

    bot_db.commit()
    bot_db.close()

    await ctx.respond("Meetup updated!")

@meetups.command(description = "See the available meetups!")
async def list_meetups(ctx):
    result = ""
    bot_db, cur = get_db()
    for row in cur.execute("SELECT * FROM MEETUPS"):
        print(row)
        result += f"{row[0]}, {row[2]}, {row[3]}, {row[4]}\n"
    await ctx.respond(result)