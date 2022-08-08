from constants_imports_utils import *

birthdays = bot.create_group("birthdays", "For telling your friends that they are now one year older! D:")


async def birthday_loop():
    
    while True:

        tmwdatetime = dt.datetime.combine(dt.date.today() + dt.timedelta(days = 1), dt.time(microsecond = 10000))
        wait_sec = dt.timedelta(seconds = (tmwdatetime - dt.datetime.now()).seconds, microseconds = (tmwdatetime - dt.datetime.now()).microseconds)
        log.info(f"We will update the birthday again on {dt.datetime.now() + wait_sec}.")
        await asyncio.sleep(wait_sec.seconds + wait_sec.microseconds)
        
        # When it is midnight, run this routine:
        log.info(f"Oh boy, it's time to report birthdays for the date {dt.date.today().strftime('%d/%m')}!")
        bot_db, cur = get_db()
        guild, guild_channel_list = await init_guild_variables()

        birthday_babies = cur.execute("SELECT * FROM birthdays WHERE date = ?", (dt.date.today().strftime("%d/%m"),)).fetchall()
        
        log.info(f"Here are our birthday babies: {birthday_babies}")
        if len(birthday_babies):
            birthday_message = ""
            for user, _ in birthday_babies:
                birthday_message += f"{user}\n"
            
            birthday_embed = discord.Embed(
                                            color = BIRTHDAY_CFG["embed_color"],
                                            title = "Wish our dear friends a happy birthday!",
                                            description = birthday_message
                                            )
            
            msg_channel = discord.utils.get(guild_channel_list, name = BIRTHDAY_CFG["birthday_channel"])
            await msg_channel.send(embed = birthday_embed)
        else:
            logging.info(f"It's nobody's birthday today :(. {dt.date.today()}")
        bot_db.close()


@birthdays.command(description = "Tell the bot your birthday! To edit your birthday, tell the bot again!")
async def set_birthday(ctx: discord.ApplicationContext, date: str):
    
    log.info(f"{ctx.author.name} is trying to set their birthday.")
    bot_db, cur = get_db()

    # We used to have a regex for this. But attempting a try-catch clause is simpler.
    try:
        day, month = map(int, date.split("/"))
        dummy_date = dt.datetime(year = 2000, month = month, day = day)
    except Exception as e:
        await ctx.send_response("That's not a birthday I can recognize! (I now accept dd/mm, d/m, dd/m, d/mm formats, e.g. for 5 Aug, type '5/08', '05/8', '5/8', or '05/08')", ephemeral = True)
        log.warning(f"{ctx.author.name} sent an invalid birthday.")
    else:
        day, month = date.split("/")
        if len(day) == 1: day = "0" + day
        if len(month) == 1: month= "0" + month
        date = day + "/" + month
        if len(cur.execute("SELECT * FROM birthdays WHERE user = ?", (ctx.author.mention,)).fetchall()):
            # The user presumably wants to edit their birthday, in which case we oblige.
            cur.execute("UPDATE birthdays SET date = ? WHERE user = ?", (date, ctx.author.mention))
            await ctx.send_response("I've updated your birthday!", ephemeral = True)
        else:
            # Key the date into the database.
            cur.execute("INSERT INTO birthdays (user, date) VALUES (?, ?)", (ctx.author.mention, date))
            await ctx.send_response("That's a nice birthday! Now you can look forward to me announcing your birthday I guess.", ephemeral = True)
            
    bot_db.commit()
    bot_db.close()

@birthdays.command(description = "Remove your birthday D:")
async def remove_birthday(ctx: discord.ApplicationContext):
    
    bot_db, cur = get_db()

    log.info(f"{ctx.author.name} is trying to remove their birthday.")
    
    if not len(cur.execute("SELECT * FROM birthdays WHERE user = ?", (ctx.author.mention,)).fetchall()):
        await ctx.send_response("HAH! You can't delete your birthday if I don't remember it!", ephemeral = True)
        log.info(f"I didn't know {ctx.author.name}'s birthday.")
    else:
        cur.execute("DELETE FROM birthdays WHERE user = ?", (ctx.author.mention,))
        await ctx.send_response("I do not remember your birthday anymore D:", ephemeral = True)
        log.info(f"{ctx.author.name} has removed their birthday.")
    
    bot_db.commit()
    bot_db.close()
    
