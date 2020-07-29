import os, os.path
import discord
from discord import NotFound
from discord.ext import commands
import sys
import random
import re
import errno
from datetime import datetime
from dotenv import load_dotenv
from file_read_backwards import FileReadBackwards
from resources.utilityMethods import Utilities

load_dotenv()  # loads .env file in the same directory -- use for configs and any changes -- dont edit settings in this file, use the env file
TOKEN = os.getenv('DISCORD_TOKEN')  # loads PRIVATE discord token that we set as an env variable in the .env file -- this is done so you don't post private token to VCs software i.e github
gServerName = os.getenv('DISCORD_GUILD')  # guild is an object referencing the server the bot/users are in, just returning the 'main' server for our worst commands
adjectiveFile = os.getenv('ADJ_BANK')
nounFile = os.getenv("NOUN_BANK")
wordBankFile = os.getenv('WORD_BANK')
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

@CLIENT.event
async def on_message(message):
    if message.author == CLIENT.user:
        return  # --No self-loops
    if message.guild.name == gServerName:
        random.seed()
        randVal = random.randint(1, 1000)
        if randVal > 995:
            response = UTILITIES.generateTownMessage(adjectiveFile, nounFile)
            await message.channel.send(response)
        if randVal == 2:
            await message.guild.me.edit(nick=secretMorphName)
            with open(secretMorph, 'rb') as f:
                image = f.read()
            await CLIENT.user.edit(avatar=image)
            f.close()
            MentionAuth = message.author.mention
            MorphResponse = f"{MentionAuth} Hello. {secretMorphMsg}"
            await message.channel.send(MorphResponse)

        pattern = "(.*)(99!+)(.*)"
        prog = re.compile(pattern)
        result = prog.match(message.content)
        if result != None:
            with open(wordBankFile, encoding="utf8") as inp:  # always pass encoding in when opening a file, or else emojis and special chars fail and shit your text up
                lines = inp.readlines()
                random_line = random.randint(0, len(
                    lines) - 1)  # ensures our random line is within proper bounds, no OOB tricks here speedrunners
                response = lines[random_line]  # pick a random line :) only reason I don't use my predefined method is to not strip text
            await message.channel.send(response)

    UrlPattern = "((http|https)\:\/\/)?[a-zA-Z0-9\.\/\?\:@\-_=#]+\.([a-zA-Z]){2,6}([a-zA-Z0-9\.\&\/\?\:@\-_=#])*"  # don't fucking ask
    UrlRegEx = re.compile(UrlPattern)
    UrlMatch = UrlRegEx.match(message.content)

    if len(message.attachments) > 0 or UrlMatch != None:
        await message.add_reaction('🔁')  # retweet :)
        await message.add_reaction('❤')  # like :)

    if message.content.lower().find("all my homies") != -1:
        await message.add_reaction('🔁')  # retweet in solidarity with ur homie
    if(message.content.find("cumtown") == -1 ) or (message.content.find("append") == -1) or (message.guild.name == gServerName):
        await CLIENT.process_commands(message) #process all the actual commands x)

async def convertToEmojiAndReact(ctx, value):
    numEmojiDict = ["0️⃣", "1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣"]
    if(value%11 == 0):
        value += 1
    for digit in list(str(value)):
        await ctx.message.add_reaction(numEmojiDict[int(digit)])                #display your cooldown as a reaction :)


@CLIENT.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.message.add_reaction("🕒")
        numFinder = str(error).split(" ")                                       #error is a type that can be converted to a str thanks to being compatible with send
        for val in numFinder:
            if val.partition(".")[0].isdigit():
                await convertToEmojiAndReact(ctx, int(val.partition(".")[0]))        #remove any decimal stuff and also any unit (i.e s for seconds)
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.message.channel.send("How about you actually give me an input")
        await ctx.message.add_reaction('❌')

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
    UTILITIES.populateCache(ctx.message,"reminder")
    await ctx.message.add_reaction('✅')

@CLIENT.command()
async def cacheimagines(ctx):
    await UTILITIES.populateCache(ctx.message,"imagine")
    await ctx.message.add_reaction('✅')

CLIENT.run(TOKEN)  # turn bot on -- buy the bot dinner prior to this step