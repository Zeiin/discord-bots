import os, os.path
import discord
from discord import NotFound
from discord.ext import commands
import sys
import random
import re
import errno
import datetime
import time
import requests
import shutil
import pyimgur
import pathlib
import boto3
import uuid
import imageio
import PIL
import subprocess
from botocore.exceptions import NoCredentialsError
from PIL import Image
from dotenv import load_dotenv
from file_read_backwards import FileReadBackwards
from resources.utilityMethods import Utilities
PIL.Image.MAX_IMAGE_PIXELS = None

load_dotenv()  # loads .env file in the same directory -- use for configs and any changes -- dont edit settings in this file, use the env file
TOKEN = os.getenv('DISCORD_TOKEN')  # loads PRIVATE discord token that we set as an env variable in the .env file -- this is done so you don't post private token to VCs software i.e github
gServerName = os.getenv('DISCORD_GUILD')  # guild is an object referencing the server the bot/users are in, just returning the 'main' server for our worst commands
IMGUR_API_ID = os.getenv('IMGUR_API_ID')
IMGUR_API_SECRET = os.getenv('IMGUR_API_SECRET')
AWS_CLIENT_ID = os.getenv('AWS_ID')
AWS_SECRET_KEY = os.getenv('AWS_SECRET')
CDN_DOMAIN = os.getenv('CDN_DOMAIN')
BUCKET = os.getenv('BUCKET')
adjectiveFile = os.getenv('ADJ_BANK')
nounFile = os.getenv("NOUN_BANK")
wordBankFile = os.getenv('WORD_BANK')
testTimer = os.getenv('TEST_TIMER')
secretMorph = os.getenv("MORPH_DIR")
secretMorphName = os.getenv("MORPH_NAME")
secretMorphMsg = os.getenv("MORPH_MSG")
CLIENT = commands.Bot(command_prefix=os.getenv("BOT_PREFIX"))
UTILITIES = Utilities()

@CLIENT.event
async def on_ready():  # api flags on_ready when the bot connects and all overhead is complete
    # GUILD = next((guild for guild in CLIENT.guilds if guild.name == gServerName), None) #---Base python's way of searching through a list and assigning a value.
    GUILD = discord.utils.find(lambda g: g.name == gServerName, CLIENT.guilds)  # -Discord Utility Function for finding a value. Easier to write ig
    print(
        f'{CLIENT.user} is connected to the following guild:\n'  # Confirming where it's connected to. No reason to print its own identity though.
        f'{GUILD.name}(id: {GUILD.id})\n'
    )
    try:  # EAFP principle in python, try to make the dir and if error aside from already exists occurs raise, otherwise ignore
        os.makedirs("resources/Widen")
    except OSError as e:
        if e.errno != errno.EEXIST:  # Only raise exception if the error is NOT that the directory already exists
            raise
    try:  # EAFP principle in python, try to make the dir and if error aside from already exists occurs raise, otherwise ignore
        os.makedirs("resources/WidenGif")
    except OSError as e:
        if e.errno != errno.EEXIST:  # Only raise exception if the error is NOT that the directory already exists
            raise
    try:  # EAFP principle in python, try to make the dir and if error aside from already exists occurs raise, otherwise ignore
        os.makedirs("resources/speedGif")
    except OSError as e:
        if e.errno != errno.EEXIST:  # Only raise exception if the error is NOT that the directory already exists
            raise

@CLIENT.event
async def on_message(message):
    if message.author == CLIENT.user:
        return  # --No self-loops

    UrlPattern = "((http|https)\:\/\/)?[a-zA-Z0-9\.\/\?\:@\-_=#]+\.([a-zA-Z]){2,6}([a-zA-Z0-9\.\&\/\?\:@\-_=#])*"  # don't fucking ask
    UrlRegEx = re.compile(UrlPattern)
    UrlMatch = UrlRegEx.match(message.content)

    if len(message.attachments) > 0 or UrlMatch != None:
        await message.add_reaction('🔁')  # retweet :)
        await message.add_reaction('❤')  # like :)

    if message.content.lower().find("all my homies") != -1:
        await message.add_reaction('🔁')  # retweet in solidarity with ur homie

    if((message.content.find(os.getenv("BOT_PREFIX")) == 0) and (message.content.lower().find("test")) > 0):

        await testLastMembersinChat(message)
    if message.guild.name == gServerName:
        random.seed()
        randVal = random.randint(1, 1000)
        if randVal > 995:
            response = UTILITIES.generateTownMessage(adjectiveFile, nounFile)
            await message.channel.send(response)
        """if randVal == 2:
            await message.guild.me.edit(nick=secretMorphName)
            with open(secretMorph, 'rb') as f:
                image = f.read()
            await CLIENT.user.edit(avatar=image)
            f.close()
            MentionAuth = message.author.mention
            MorphResponse = f"{MentionAuth} Hello. {secretMorphMsg}"
            await message.channel.send(MorphResponse)
        """
        pattern = "(.*)(99!+)(.*)"
        prog = re.compile(pattern)
        result = prog.match(message.content)
        if result != None:
            with open(wordBankFile, encoding="utf8") as inp:  # always pass encoding in when opening a file, or else emojis and special chars fail and shit your text up
                lines = inp.readlines()
                random_line = random.randint(0, len(lines) - 1)  # ensures our random line is within proper bounds, no OOB tricks here speedrunners
                response = lines[random_line]  # pick a random line :) only reason I don't use my predefined method is to not strip text
            await message.channel.send(response)

    if((message.content.find("cumtown") == -1 ) and (message.content.find("append") == -1)) or (message.guild.name == gServerName):
        await CLIENT.process_commands(message) #process all the actual commands x)

async def convertToEmojiAndReact(ctx, value):
    numEmojiDict = ["0️⃣", "1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣"]
    if(value%11 == 0):
        value += 1
    for digit in list(str(value)):
        await ctx.message.add_reaction(numEmojiDict[int(digit)])                #display your cooldown as a reaction :)

async def getLastMembersinChat(message, timeLimit):
    relevantAuthorList = []                                                             #declare empty list for obvious reasons
    afterVal = datetime.datetime.now() - datetime.timedelta(minutes=timeLimit)          #note that these both have to be naive, if you make .now() aware you can't use timedelta, pretty fucking silly if you ask me haha :)
    print(f'{afterVal}\n')
    async for curMESSAGE in message.channel.history(limit=None,before=message,after=afterVal):                #after doesn't care about the time, these params handle the edge case of a dead server instead of a ridiculously long loop..
        if(curMESSAGE.created_at >= afterVal):
            if (not curMESSAGE.author in relevantAuthorList) and curMESSAGE.author != curMESSAGE.guild.me:      #don't include yourself (you being the bot) in this check, you'd fail every test
                relevantAuthorList.append(curMESSAGE.author)
        else:
            break
    return relevantAuthorList

async def testLastMembersinChat(message):
    AuthorList = await getLastMembersinChat(message, 5)
    targetTest = re.search('!(.*)test', message.content.lower()).group(1).upper().rstrip().upper()                  #picking the "test" target i.e !TARGETtest would make our target "TARGET"
    afterVal = await message.channel.send(f'{targetTest} TEST STARTING NOW, YOU HAVE {testTimer} SECONDS TO SEND A MESSAGE INCLUDING "NOT A {targetTest}" (case insensitive) OR YOU\'LL BE DEEMED A {targetTest}')
    time.sleep(int(testTimer))
    await message.channel.send(f'GRADING {targetTest} TESTS.')
    async for curMESSAGE in message.channel.history(limit=None,after=afterVal):
        print(f'{curMESSAGE.content}\n')
        if (curMESSAGE.content.lower().find(f'not a {targetTest.lower()}') >= 0) and curMESSAGE.author in AuthorList:
            if (curMESSAGE.content.lower().partition(targetTest.lower())[0].count("not") % 2 != 0):
                AuthorList[:] = [Authors for Authors in AuthorList if curMESSAGE.author != Authors]
                await curMESSAGE.add_reaction('✅')
            else:
                await curMESSAGE.add_reaction('❌')
    FailureList = []
    for Authors in AuthorList:
        FailureList.append(Authors.mention)
    Quantifier = "IS A"
    if len(FailureList) > 1:
        if (targetTest[len(targetTest) - 1].lower() == 'h') and (targetTest[len(targetTest) - 2].lower() == 'c'):
            targetTest += 'E'
        targetTest += 'S'
        Quantifier = "ARE BOTH"
        if len(FailureList) > 2:
            Quantifier = "ARE ALL"

    if len(FailureList) > 0:
        await message.channel.send(f'{", ".join(FailureList)} {Quantifier} {targetTest}')
    else:
        await message.channel.send(f'EVERYONE PASSED. NOBODY IS A {targetTest}')

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
        #await ctx.send(error)

@CLIENT.command()
@commands.cooldown(1, 60, commands.BucketType.user)
async def cumtown(ctx):
    response = UTILITIES.generateTownMessage(adjectiveFile, nounFile)
    await ctx.message.channel.send(response)

@CLIENT.command()
async def appendadj(ctx, *, arg):
    if(len(arg) > 0):
        UTILITIES.appendToFileWeirdly(arg, adjectiveFile)
        await ctx.message.add_reaction('✅')

@CLIENT.command()
async def appendnoun(ctx, *, arg):
    if (len(arg) > 0):
        UTILITIES.appendToFileWeirdly(arg, nounFile)
        await ctx.message.add_reaction('✅')

@CLIENT.command(aliases=['remindme'])
@commands.cooldown(1, 60, commands.BucketType.user)
async def reminder(ctx):
    reminderData = UTILITIES.pullFromCache(ctx.message, "reminder")
    await ctx.message.channel.send(content=reminderData[0],files=reminderData[1])  # syntax for sending a message with both text and files

@CLIENT.command(aliases=['imagineme'])
@commands.cooldown(1, 60, commands.BucketType.user)
async def imagine(ctx):
    reminderData = UTILITIES.pullFromCache(ctx.message, "imagine")
    await ctx.message.channel.send(content=reminderData[0],files=reminderData[1])  # syntax for sending a message with both text and files
""" USE BELOW IF YOU WANT TO SEPARATE THE COOLDOWNS OF REMIND/IMAGINE AND REMINDME/IMAGINEME COMMANDS
@CLIENT.command()
@commands.cooldown(1, 60, commands.BucketType.user)
async def remindme(ctx):
    reminder(ctx)
    #reminderData = UTILITIES.pullFromCache(ctx.message, "reminder")
    #await ctx.message.channel.send(content=reminderData[0],files=reminderData[1])  # syntax for sending a message with both text and files

@CLIENT.command()
@commands.cooldown(1, 60, commands.BucketType.user)
async def imagineme(ctx):
    reminderData = UTILITIES.pullFromCache(ctx.message, "imagine")
    await ctx.message.channel.send(content=reminderData[0],files=reminderData[1])  # syntax for sending a message with both text and files
"""
@CLIENT.command()
async def cachereminders(ctx):
    await UTILITIES.populateCache(ctx.message,"reminder")
    await ctx.message.add_reaction('✅')

@CLIENT.command()
async def cacheimagines(ctx):
    await UTILITIES.populateCache(ctx.message,"imagine")
    await ctx.message.add_reaction('✅')

@CLIENT.command(aliases=['ultrawiden', 'nocropwiden'])
async def widen(ctx, *args):
    filName = ""
    imgName = ""
    discrim = uuid.uuid1()
    if(len(args) == 0):
        if(len(ctx.message.attachments) > 0):
            for attachment in ctx.message.attachments:  # check for files attached
                filName = f'resources/Widen/{discrim}{attachment.filename}'
                imgName = f'{discrim}{attachment.filename}'
                await attachment.save(filName)  # save the file-like object, must be converted to discord file on use
    else:
        #imageURL = embeds.thumbnail.url
        imageURL = args[0]
        imageReq = requests.get(imageURL, stream=True)              #download image from the url using requests because it has a good user-header unlike urlrequest
        if imageReq.status_code == 200:
            imgName = imageURL.split('/')[-1].partition('?')[0]
            filName = f"resources/Widen/{discrim}{imgName}"
            with open(filName, 'wb') as f:
                imageReq.raw.decode_content = True
                shutil.copyfileobj(imageReq.raw, f)
    imageExtensions = ['.jpg', '.png', '.jpeg', '.bmp', '.webp']
    validImage = False
    for ext in imageExtensions:
        if filName.endswith(ext):
            validImage = True
    if validImage == True:
        UTILITIES.widenImage(filName, 2 if ctx.message.content.find('ultra') > -1 else 1, 1 if ctx.message.content.find('nocrop') > -1 else 0)
        await ctx.send(content=f'{ctx.author.mention}', file=discord.File(filName))
    elif filName.endswith('.gif'):
        filName2 = f'resources/Widen/{discrim}.gif'
        UTILITIES.processGifImage(filName, 2 if ctx.message.content.find('ultra') > -1 else 1, 1 if ctx.message.content.find('nocrop') > -1 else 0)
        os.rename(filName, filName2)
        cdnURL = UTILITIES.upload_file(filName2, BUCKET, AWS_CLIENT_ID, AWS_SECRET_KEY, CDN_DOMAIN)
        if(cdnURL != None):
            await ctx.send(content=f'{ctx.author.mention} {cdnURL}')
        else:
            await ctx.send("some shit went wrong when uploaded gif to web server.. tell zein to check it later")
        try:
            os.remove(filName2)
        except OSError as e:
            if e.errno != errno.ENOENT and e.errno != errno.EPERM:
                raise
    else:
        await ctx.send(f'{ctx.author.mention} please send a valid image file.')
    try:
        os.remove(filName)
    except OSError as e:
        if e.errno != errno.ENOENT and e.errno != errno.EPERM:
            raise

@CLIENT.command(aliases=['ultrawidenavatar', 'ultrawideavatar', 'wideavatar'])
async def widenavatar(ctx, user: discord.Member):
    filName = ""
    imgName = ""
    discrim = uuid.uuid1()
    userAvatar = user.avatar_url
    imageReq = requests.get(userAvatar, stream=True)  # download image from the url using requests because it has a good user-header unlike urlrequest
    if imageReq.status_code == 200:
        imgName = str(userAvatar).split('/')[-1].partition('?')[0]
        filName = f"resources/Widen/{discrim}{imgName}"
        with open(filName, 'wb') as f:
            imageReq.raw.decode_content = True
            shutil.copyfileobj(imageReq.raw, f)

    if filName.endswith("gif"):
        filName2 = f'resources/Widen/{discrim}.gif'
        UTILITIES.processGifImage(filName, 2 if ctx.message.content.find('ultra') > -1 else 1, 1 if ctx.message.content.find('nocrop') > -1 else 0)
        os.rename(filName, filName2)
        cdnURL = UTILITIES.upload_file(filName2, BUCKET, AWS_CLIENT_ID, AWS_SECRET_KEY, CDN_DOMAIN)
        if (cdnURL != None):
            await ctx.send(content=f'{ctx.author.mention} {cdnURL}')
        else:
            await ctx.send("some shit went wrong when uploaded gif to web server.. tell zein to check it later")
        try:
            os.remove(filName2)
        except OSError as e:
            if e.errno != errno.ENOENT and e.errno != errno.EPERM:
                raise
    elif filName.endswith("jpg") or filName.endswith("webp") :
        UTILITIES.widenImage(filName, 2 if ctx.message.content.find('ultra') > -1 else 1, 1 if ctx.message.content.find('nocrop') > -1 else 0)
        await ctx.send(content=f'{ctx.author.mention}', file=discord.File(filName))
    else:
        await ctx.send(f'{ctx.author.mention} Sorry, I couldn\'t grab the requested user\'s avatar')
    try:
        os.remove(filName)
    except OSError as e:
        if e.errno != errno.ENOENT and e.errno != errno.EPERM:
            raise

@CLIENT.command(aliases=['slowdown', 'emspeeden'])
async def speedup(ctx, *args):
    filName = ""
    imgName = ""
    discrim = uuid.uuid1()
    if (len(args) == 0):
        if (len(ctx.message.attachments) > 0):
            for attachment in ctx.message.attachments:  # check for files attached
                filName = f'resources/speedGif/{discrim}{attachment.filename}'
                await attachment.save(filName)  # save the file-like object, must be converted to discord file on use
    else:
        imageURL = args[0]
        imageReq = requests.get(imageURL,stream=True)  # download image from the url using requests because it has a good user-header unlike urlrequest
        if imageReq.status_code == 200:
            imgName = imageURL.split('/')[-1].partition('?')[0]
            filName = f"resources/speedGif/{discrim}{imgName}"
            with open(filName, 'wb') as f:
                imageReq.raw.decode_content = True
                shutil.copyfileobj(imageReq.raw, f)
    if filName.find('.gif') > 0:
        filName2 = f'resources/speedGif/{discrim}.gif'
        retVal = imageio.mimread(filName, memtest=False)
        frameDelays = []
        frameData = []
        for metaData in retVal:
            curDelay = metaData.meta["duration"] * (0.5 if ctx.message.content.find('speed') > 0 else 2) * 0.001
            frameDelays.append(curDelay if curDelay > 0.02 else 0.02)
            frameData.append(metaData)
            #print(f'{metaData.meta["duration"] * (0.5 if ctx.message.content.find("speed") > 0 else 2)}')
        imageio.mimsave(filName2, frameData,duration=frameDelays)
        cdnURL = UTILITIES.upload_file(filName2, BUCKET, AWS_CLIENT_ID, AWS_SECRET_KEY, CDN_DOMAIN)
        if (cdnURL != None):
            await ctx.send(content=f'{ctx.author.mention} {cdnURL}')
        else:
            await ctx.send("some shit went wrong when uploaded gif to web server.. tell zein to check it later")
    else:
        await ctx.send("Please give me a gif.")
    try:
        os.remove(filName)
        os.remove(filName2)
    except OSError as e:
        if e.errno != errno.ENOENT:
            raise

@CLIENT.command(aliases=['avatar'])
async def getavatar(ctx, user: discord.Member):
    userAvatar = user.avatar_url
    await ctx.send(userAvatar)
"""
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
"""
CLIENT.run(TOKEN)  # turn bot on -- buy the bot dinner prior to this step

