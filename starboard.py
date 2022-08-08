# Starboard checker.
from constants_imports_utils import *


async def check_sb(payload: discord.RawReactionActionEvent):
    
    # print(payload)
    channel, sb_msg = await get_message_from_payload(payload)
    guild, guild_channel_list = await init_guild_variables()
    # print(sb_msg.reactions, sb_msg.content)

    sb_channel = discord.utils.get(guild_channel_list, name = STARBOARD_CFG["starboard_channel"])
    
    for reaction in sb_msg.reactions:
        # print(payload.emoji, reaction, str(payload.emoji) == str(reaction), reaction.count >= STARBOARD_CFG["min_count"])
        if str(payload.emoji) == str(reaction) \
            and reaction.count >= STARBOARD_CFG["min_count"] \
            and not sb_msg.author.bot \
            and sb_msg.channel != sb_channel:

                sb_embed = discord.Embed(
                        color = STARBOARD_CFG["embed_color"],
                        title = "IS A STAR!",
                        description = f"[Link]({sb_msg.jump_url})\n" + sb_msg.content
                        )
                
                sb_embed.set_author(name = sb_msg.author, icon_url = sb_msg.author.display_avatar)
                
                if len(sb_msg.attachments) > 0:
                    sb_embed.set_image(url = sb_msg.attachments[0].url)
                
                sb_embed.timestamp = sb_msg.created_at

                
                async for msg in sb_channel.history(limit = None):
                    # Yes. I understand it doesn't update when a react is removed. 
                    # But you know, nobody's REALLY keeping track of HOW MANY STARS a message has, and this is an expensive operation.
                    if str(sb_msg.id) in msg.content:
                        await msg.edit(f"({reaction.count} ⭐) A star has appeared in {sb_channel.mention}! (ID: {sb_msg.id})", embed = sb_embed)
                        return None

                await sb_channel.send(f"({reaction.count} ⭐) A star has appeared in {sb_channel.mention}! (ID: {sb_msg.id})", embed = sb_embed)

                return None

