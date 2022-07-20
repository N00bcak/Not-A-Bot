from setup import *
import discord
async def pin(react: discord.RawReactionActionEvent):

    # Basically, when a specific emoji is given as a reaction to a message, pin the message.
    # Requires ManageMessages permission.
    
    channel, reacted_msg = await get_message_from_payload(react)

    # print(channel, reacted_msg)
    await reacted_msg.pin(reason = f"Pinned by {react.member.name} through the bot.")


async def unpin(react: discord.RawReactionActionEvent):
    
    # The converse of the pin function.

    channel, reacted_msg = await get_message_from_payload(react)
    
    # channel = bot.get_channel(react.channel_id)
    # reacted_msg = await channel.fetch_message(react.message_id)

    unpin = True
    
    for pin_emoji in PIN_MSGS_CFG['emoji_list']:
        if react.emoji.name in map(lambda x: str(x), reacted_msg.reactions): unpin = False
    
    if unpin: await reacted_msg.unpin(reason = f"Unpinned through the bot.")
    