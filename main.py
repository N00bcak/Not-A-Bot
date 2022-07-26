from constants_imports_utils import *
import private_utils
import pin_msgs
import starboard
import meetups_handler
import birthday_handler
import image_flipper

# This main file is the principal event listener for the bot. I'm not quite sure how to structure a file so here's how it's gonna go.
# Using decorators because its more straightforward. 
# Maybe in the future we will implement a subclass which overrides the functionality of the Client superclass.

@bot.event
async def on_message(message):
    flag = await private_utils.func1(message)

@bot.event
async def on_raw_message_edit(payload):
    flag = await private_utils.func2(payload)

@bot.event
async def on_raw_reaction_add(payload):
    flag = await private_utils.func3(payload)
    if not flag:
        # The emoji checks are done here, so the functions themselves don't need to ascertain the identity of the emoji.
        if payload.emoji.name in PIN_MSGS_CFG["emoji_list"]:
            await pin_msgs.pin(payload)
        elif payload.emoji.name in STARBOARD_CFG["emoji_list"]:
            await starboard.check_sb(payload)

@bot.event
async def on_raw_reaction_remove(payload):
    
    # The emoji checks are done here, so the functions themselves don't need to ascertain the identity of the emoji.
    if payload.emoji.name in PIN_MSGS_CFG["emoji_list"]:
        await pin_msgs.unpin(payload)

@bot.event
async def on_ready():
    log.info(f"{bot.user} has connected to Discord!")
    guild, guild_channel_list = await init_guild_variables()
    log.info(f"We in the {guild.name} server.")
    await meetups_handler.refresh_meetups()
    await birthday_handler.birthday_loop()
    
bot.run(TOKEN)
