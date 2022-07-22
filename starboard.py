# Starboard checker.
from constants_imports_utils import *


async def check_sb(payload):
    
    channel, sb_msg = await get_message_from_payload(payload)

    print(sb_msg.reactions)

    for reaction in sb_msg.reactions:
        # print(payload.emoji, reaction, str(payload.emoji) == str(reaction), reaction.count)
        if str(payload.emoji) == str(reaction.emoji) and reaction.count >= STARBOARD_CFG["min_count"]:
            sb_embed = discord.Embed(
                                color = STARBOARD_CFG["embed_color"],
                                title = "IS A STAR!",
                                description = f"[Link]({sb_msg.jump_url})\n" + sb_msg.content
                                )
            sb_embed.set_author(name = sb_msg.author, icon_url = sb_msg.author.display_avatar)
            
            if len(sb_msg.attachments) > 0:
                sb_embed.set_image(url = sb_msg.attachments[0].url)

            sb_embed.timestamp = sb_msg.created_at

            sb_channel = discord.utils.get(bot.get_all_channels(), name = STARBOARD_CFG["starboard_channel"])

            print(sb_channel)

            await sb_channel.send(f"A star has appeared in {sb_channel.mention}!", embed = sb_embed)
            return None

