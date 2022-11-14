from constants_imports_utils import *
import discord
async def pin(react: discord.RawReactionActionEvent):

    # Basically, when a specific emoji is given as a reaction to a message, pin the message.
    # Requires ManageMessages permission.
    # EDIT: Because of the 50-pin limitation per channel on discord, this function will now automatically wipe the oldest pinned message upon pinning if the pin limit is reached.

    channel, reacted_msg = await get_message_from_payload(react)

    # Maybe I should catch this error.
    pinned_messages = await channel.pins()
    pinned_messages.sort(key = lambda x: x.created_at)
    log.info(f"No. of pinned messages in channel {channel.name}: {len(pinned_messages)}")
    
    if len(pinned_messages) == 50: pinned_messages[0].unpin(reason = f"Unpinned through the bot.")
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
    