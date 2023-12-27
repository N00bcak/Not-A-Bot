from NotABot.common import bot, log, TOKEN, cfg, general_utils
from NotABot.server_misc import pin_msgs, starboard, meetups_handler, birthday_handler, image_flipper
from NotABot.minigames import blackjack

# This main file is the principal event listener for the bot. I'm not quite sure how to structure a file so here's how it's gonna go.
# Using decorators because its more straightforward.
# Maybe in the future we will implement a subclass which overrides the functionality of the Client superclass.

@bot.event
async def on_message(message):
    #flag = await private_utils.func1(message)
    pass
@bot.event
async def on_raw_message_edit(payload):
    #flag = await private_utils.func2(payload)
    pass
@bot.event
async def on_raw_reaction_add(payload):
    #flag = await private_utils.func3(payload)
    #if not flag:
    # The emoji checks are done here, so the functions themselves don't need to ascertain the identity of the emoji.
    if payload.emoji.name in cfg.PIN_MSGS_CFG["emoji_list"]:
        await pin_msgs.pin(payload)
    elif payload.emoji.name in cfg.STARBOARD_CFG["emoji_list"]:
        await starboard.check_sb(payload)

@bot.event
async def on_raw_reaction_remove(payload):
    
    # The emoji checks are done here, so the functions themselves don't need to ascertain the identity of the emoji.
    if payload.emoji.name in cfg.PIN_MSGS_CFG["emoji_list"]:
        await pin_msgs.unpin(payload)

@bot.event
async def on_ready():
    log.info(f"{bot.user} has connected to Discord!")
    #print(bot.commands)
    guild, guild_channel_list = await general_utils.init_guild_variables()
    log.info(f"We in the {guild.name} server.")

    await meetups_handler.refresh_meetups()
    await birthday_handler.birthday_loop()

bot.run(TOKEN)
