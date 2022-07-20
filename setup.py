import discord
import os
import dotenv

dotenv.load_dotenv()

# Store your secrets in a .env file!
TOKEN = os.getenv("BOT_TOKEN")
GUILD = os.getenv("GUILD_ID")
SECRET = [int(id_num) for id_num in  os.getenv("SECRET").split(',')]

# Client object for the Discord bot.
bot = discord.Client()

# Configuration for pin_msgs.py
PIN_MSGS_CFG = {
                "emoji_list": ['📌','📍']
                }

# Configurations for starboard.py
STARBOARD_CFG= {
                "emoji_list": ['a_'], 
                "min_count": 1, 
                "embed_color": 0xFAD905, 
                "starboard_channel": "starboard"
                }

#⭐

# Basic utility functions
async def get_message_from_payload(payload):
    channel = bot.get_channel(payload.channel_id)
    reacted_msg = await channel.fetch_message(payload.message_id)
    return channel, reacted_msg