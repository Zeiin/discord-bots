import os, os.path
import discord
from discord import NotFound
from discord.ext import commands
import errno
import requests
import shutil
import PIL
import subprocess
from PIL import Image
from dotenv import load_dotenv
PIL.Image.MAX_IMAGE_PIXELS = None

load_dotenv()  # loads .env file in the same directory -- use for configs and any changes -- dont edit settings in this file, use the env file
TOKEN = os.getenv('YAKUZA_TOKEN')  # loads PRIVATE discord token that we set as an env variable in the .env file -- this is done so you don't post private token to VCs software i.e github
gServerName = os.getenv('DISCORD_GUILD')  # guild is an object referencing the server the bot/users are in, just returning the 'main' server for our worst commands
CLIENT = commands.Bot(command_prefix=os.getenv("BOT_PREFIX"))

@CLIENT.event
async def on_ready():  # api flags on_ready when the bot connects and all overhead is complete
    # GUILD = next((guild for guild in CLIENT.guilds if guild.name == gServerName), None) #---Base python's way of searching through a list and assigning a value.
    GUILD = discord.utils.find(lambda g: g.name == gServerName, CLIENT.guilds)  # -Discord Utility Function for finding a value. Easier to write ig
    print(
        f'{CLIENT.user} is connected to the following guild:\n'  # Confirming where it's connected to. No reason to print its own identity though.
        f'{GUILD.name}(id: {GUILD.id})\n'
    )


@CLIENT.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.message.add_reaction("🕒")
        numFinder = str(error).split(" ")                                       #error is a type that can be converted to a str thanks to being compatible with send
        for val in numFinder:
            if val.partition(".")[0].isdigit():
                await convertToEmojiAndReact(ctx, int(val.partition(".")[0]))        #remove any decimal stuff and also any unit (i.e s for seconds)
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("How about you actually give me an input")
        await ctx.message.add_reaction('❌')
    else:
        print(f'{str(error)}')

@CLIENT.command()
async def bakamitai(ctx, *args):
    filName = ""
    if (len(args) == 0):
        if (len(ctx.message.attachments) > 0):
            for attachment in ctx.message.attachments:  # check for files attached
                filName = f'MLDeepFake/first-order-model/resources/BaseIMG.png'
                await attachment.save(filName)  # save the file-like object, must be converted to discord file on use
    else:
        imageURL = args[0]
        imageReq = requests.get(imageURL,stream=True)  # download image from the url using requests because it has a good user-header unlike urlrequest
        if imageReq.status_code == 200:
            filName = f'MLDeepFake/first-order-model/resources/BaseIMG.png'
            with open(filName, 'wb') as f:
                imageReq.raw.decode_content = True
                shutil.copyfileobj(imageReq.raw, f)
    if os.path.exists(filName) == True:
        im = Image.open(filName)
        im = im.resize((256, 256))
        im.save(filName)
        im.close()
        batchFileLocation = 'MLDeepFake/first-order-model'
        batchFileFullPath = os.path.join(batchFileLocation, 'Bakamitai.bat')
        p = subprocess.Popen(os.path.abspath(batchFileFullPath), cwd = batchFileLocation)
        p.wait()
        discordFil = discord.File(f"MLDeepFake/first-order-model/finalResult.mp4")
        await ctx.send(file = discordFil)
    else:
        await ctx.send("Couldn't get that image idk why")
    try:
        os.remove(filName)
    except OSError as e:
        if e.errno != errno.ENOENT and e.errno != errno.EPERM:
            raise

CLIENT.run(TOKEN)  # turn bot on -- buy the bot dinner prior to this step

#UTILITIES.processGifImage('resources/sample.gif', 1, 0)

