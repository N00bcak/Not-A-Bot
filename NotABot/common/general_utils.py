from NotABot.common import bot, cfg, GUILD
import discord
import sqlite3
# General utility functions used by multiple files
async def get_message_from_payload(payload):
    channel = bot.get_channel(payload.channel_id)
    reacted_msg = await channel.fetch_message(payload.message_id)
    return channel, reacted_msg

# Guild related variables
async def init_guild_variables():
    guild = discord.utils.find(lambda x: str(x.id) == GUILD, bot.guilds)
    guild_channel_list = await guild.fetch_channels()
    return guild, guild_channel_list

# Initiates a connection with our SQLite database
def get_db():
    bot_db = sqlite3.connect(cfg.db_location)
    cur = bot_db.cursor()
    db_list = [i[0] for i in cur.execute('''SELECT name FROM sqlite_master''').fetchall()]
    
    #print(db_list)

    if "meetups" not in db_list:
        # We don't have meetups data.
        cur.execute("CREATE TABLE meetups (id, meetup_owner, message_id, meetup_desc, meetup_time, meetup_location, participants)")
    
    if "birthdays" not in db_list:
        # We don't have birthday data.
        cur.execute("CREATE TABLE birthdays (user, date)")
    
    bot_db.commit()
    return bot_db, cur
