import discord
import os
import dotenv
import logging
from NotABot.common import cfg
from discord.ext import commands

dotenv.load_dotenv()
logging.basicConfig(filename = cfg.log_location, format = '[%(asctime)s] %(message)s')
log = logging.getLogger()
log.setLevel(logging.INFO)

# Store your secrets in a .env file!
TOKEN = os.getenv("BOT_TOKEN")
GUILD = os.getenv("GUILD_ID")
SECRET = [int(id_num) for id_num in os.getenv("SECRET").split(',')]

# Client object for the Discord bot.
intents = discord.Intents.all()
intents.members = True
intents.message_content = True
bot = discord.Bot(debug_guilds = [GUILD], intents = intents)
# bot = commands.Bot(command_prefix = "??", guilds = [GUILD], intents = intents)