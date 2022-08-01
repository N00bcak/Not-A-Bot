import discord
import os
import dotenv
import sqlite3
import json
import re

dotenv.load_dotenv()

# Store your secrets in a .env file!
TOKEN = os.getenv("BOT_TOKEN")
GUILD = os.getenv("GUILD_ID")
SECRET = [int(id_num) for id_num in os.getenv("SECRET").split(',')]

# Client object for the Discord bot.
intents = discord.Intents.default()
intents.members = True
bot = discord.Bot(debug_guilds = [GUILD], intents = intents)

# Configuration for pin_msgs.py
PIN_MSGS_CFG = {
                "emoji_list": ['📌','📍']
                }

# Configuration for starboard.py
STARBOARD_CFG = {
                "emoji_list": ['⭐'], 
                "min_count": 12, 
                "embed_color": 0xFAD905, 
                "starboard_channel": "starboard"
                }

# Configuration for meetups_handler.py
MEETUPS_CFG = {
                "embed_color": 0x84F20F,
                "meetups_channel": "starboard"
                }


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
    bot_db = sqlite3.connect("storage.db")
    cur = bot_db.cursor()
    db_list = [i[0] for i in cur.execute('''SELECT name FROM sqlite_master''').fetchall()]
    
    print(db_list)

    if "meetups" not in db_list:
        # We don't have meetups data.
        cur.execute("CREATE TABLE meetups (id, meetup_owner, message_id, meetup_desc, meetup_time, meetup_location, participants)")
    
    # TODO: Birthday tracker. Probably simple enough but I'm out of time today.
    if "birthdays" not in db_list:
        # We don't have birthday data.
        cur.execute("CREATE TABLE birthdays (user, date)")
    
    bot_db.commit()
    return bot_db, cur
