from NotABot.common import bot
import discord
import requests
from PIL import Image, ImageChops
import io

@bot.command(description = "Flip an image to spare your necks (only supports right angle turns atm)!")
async def image_flip(ctx: discord.ApplicationContext, \
                    msg_id: discord.Option(str, description = "What is the ID of the message containing the image you want to flip?"), \
                    orientation: discord.Option(str, description = "Turn your image 'left', 'right', or 'invert it? (Accepts 'left', 'right', 'invert'") = "right", \
                    image_no: discord.Option(str, description = "Which image do you want to flip? (1-indexed)") = 1
                    ):
    
    # TODO: Figure out a way to make the bot work across multiple channels.
    # It seems simple enough, and indeed it's not because I CAN'T that I'm not implementing such a feature yet.
    # Rather, I'm unsure what to do with private channels as a whole, since there exists a potential security/server administration risk if private images were leaked into public channels.

    orientation_dict = {
        "left": -90,
        "right": 90,
        "invert": 180
    }

    accepted_image_formats = ["image/png", "image/jpeg", "image/jpg", "image/tiff", "image/bmp"]

    with ctx.channel.typing():
        try:
            target_message = await ctx.channel.fetch_message(int(msg_id))
        except discord.NotFound:
            await ctx.send_response("If you sent a valid message ID, I haven't figured out what to do with private channels! \nSo until then, I am only permitted to rotate images inside the channels they were sent :(\nIn the case that you DIDN'T send a proper ID, check again?)", ephemeral = True)
            return
        
        msg_images = list(filter(lambda x: x.content_type in accepted_image_formats, target_message.attachments))

        # Should I prevent spam by blocking rotations of bot images? On the grounds that that could be useful, I will not... for now...
        if not len(msg_images):
            await ctx.send_response("I could not find any valid images here (supported formats: .png, .jpg, .jpeg, .tiff, .bmp)")
        else:
            try:
                target_image = Image.open(requests.get(msg_images[int(image_no) - 1].url, stream = True).raw)
            except IndexError:
                await ctx.send_response("The image number you provided was invalid :smadge:", ephemeral = True)
                return

        try:
            await ctx.defer(invisible = False)
            # Basically, we rotate the image as desired, and try to fit the whole rotated image into the, well, Image.
            # We then use a black image to work out (approximately) where we should crop the target image.
            target_image = target_image.rotate(orientation_dict[orientation], expand = 1)
            target_image_size = (target_image.width, target_image.height)

            blackspace = Image.new(target_image.mode, target_image_size)
            scaffold = ImageChops.difference(target_image, blackspace)
            
            target_image.resize(target_image_size, box = scaffold.getbbox())
            print("Great success!")
        except KeyError:
            await ctx.send_followup("Invalid orientation >:( (Don't tell Twitter I said that.)", ephemeral = True)
            return

    with io.BytesIO() as buffer:
        target_image.save(buffer, "png")
        buffer.seek(0)
        await ctx.send_followup(file = discord.File(fp = buffer, filename = "image.png"))
