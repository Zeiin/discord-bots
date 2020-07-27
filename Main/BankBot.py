import os, os.path
import discord
import sys
import random
import re
import errno
from dotenv import load_dotenv

load_dotenv()                       #loads .env file in the same directory -- use for configs and any changes -- dont edit settings in this file, use the env file
TOKEN = os.getenv('DISCORD_TOKEN')  #loads PRIVATE discord token that we set as an env variable in the .env file -- this is done so you don't post private token to VCs software i.e github
gServerName = os.getenv('DISCORD_GUILD')  #guild is an object referencing the server the bot/users are in
wordBankFile = os.getenv('WORD_BANK')
#CLIENT = discord.Client()           #client is an object that handles all our interaction with discord -- events, state management, read/write, any api calls, etc.
#CLIENT = discord.Client()           #client is an object that handles all our interaction with discord -- events, state management, read/write, any api calls, etc.
GUILD = None

class customClient(discord.Client):
    async def on_ready(self):              #api flags on_ready when the bot connects and all overhead is complete
        #GUILD = next((guild for guild in CLIENT.guilds if guild.name == gServerName), None) #---Base python's way of searching through a list and assigning a value.
        GUILD = discord.utils.find(lambda g: g.name == gServerName, CLIENT.guilds) #-Discord Utility Function for finding a value. Easier to write ig
        print(
            f'{CLIENT.user} is connected to the following guild:\n'   #Confirming where it's connected to. No reason to print its own identity though.
            f'{GUILD.name}(id: {GUILD.id})'
        )
    async def on_message(self, message):
        if message.author == CLIENT.user:
            return #--No self-loops

        pattern = "(.*)(99!+)(.*)"
        prog = re.compile(pattern)
        result = prog.match(message.content)
        if result != None:
            with open(wordBankFile, encoding="utf8") as inp:        #always pass encoding in when opening a file, or else emojis and special chars fail and shit your text up
                lines = inp.readlines()
                random_line = random.randint(0, len(lines) - 1)     #ensures our random line is within proper bounds, no OOB tricks here speedrunners
                response = lines[random_line]                       #pick a random line :)
            await message.channel.send(response)                    #sends the random line, all coroutines must be awaited? i think at least the ones I use do.
            inp.close()

        UrlPattern = "((http|https)\:\/\/)?[a-zA-Z0-9\.\/\?\:@\-_=#]+\.([a-zA-Z]){2,6}([a-zA-Z0-9\.\&\/\?\:@\-_=#])*" #don't fucking ask
        UrlRegEx = re.compile(UrlPattern)
        UrlMatch = UrlRegEx.match(message.content)

        if len(message.attachments) > 0 or UrlMatch != None:
            await message.add_reaction('🔁')                         #retweet :)
            await message.add_reaction('❤')                         #like :)

        if message.content.lower().find("all my homies") != -1:
            await message.add_reaction('🔁')                         # retweet in solidarity with ur homie

        if message.content == "!cachereminders":                    #we cache reminders every so often instead of reading the entire message history every time we want to find a reminder
            curGUILD = message.guild                                #currentGuild to cache from
            try:                                                    #EAFP principle in python, try to make the dir and if error aside from already exists occurs raise, otherwise ignore
                os.makedirs(curGUILD.name.replace(" ", "") + "\\attachments")
            except OSError as e:
                if e.errno != errno.EEXIST:                         #Only raise exception if the error is NOT that the directory already exists
                    raise
            with open(curGUILD.name.replace(" ", "") + "\\reminderCache.txt", encoding="utf8", mode="a") as outp: #keep reminder caches seperated by folders named after each server - special characters probably not handled here..
                for curCHANNEL in curGUILD.channels:
                    if curCHANNEL.type is discord.ChannelType.text: #only loop through text channels
                        print(f'{curCHANNEL.name} is of type {curCHANNEL.type}\n')
                        async for curMESSAGE in curCHANNEL.history(limit=None): #for every message in this channel's history
                            if curMESSAGE.content.lower().find("reminder") >= 0 and curMESSAGE.content.lower().find("!") != 0 and curMESSAGE.author != CLIENT.user:
                                curVal = f'{curMESSAGE.author.mention} {curMESSAGE.content} ' #Formats the beginning of the string to mention the user and post the reminder itself
                                for attachment in curMESSAGE.attachments:                     #check for files attached
                                    random.seed()                                             #random seed so duplicate file names almost never happen
                                    filName = f'{curGUILD.name.replace(" ","")}\\attachments\\{random.randint(1,1000)}{attachment.filename}' #append random value to file name
                                    curVal += (f'|{filName}|+')                               #attaches a tag to the reminder line that indicates we have a file attachment
                                    await attachment.save(filName)                            #save the file-like object, must be converted to discord file on use
                                curVal += "\n"
                                outp.write(curVal)
                                print(curVal)
                    else:
                        print(f'{curCHANNEL.name} is of type {curCHANNEL.type}\n')
            outp.close()

        if message.content == "!reminder":
            with open(message.guild.name + "\\reminderCache.txt", encoding="utf8") as reminp:        #always pass encoding in when opening a file, or else emojis and special chars fail and shit your text up
                lines = reminp.readlines()
                random_line = random.randint(0, len(lines) - 1)     #ensures our random line is within proper bounds, no OOB tricks here speedrunners
                response = lines[random_line]                       #pick a random line :)
                attachmentsList = re.findall('\|(.*?)\|', response) #gets a list of all attachments possible, assumption based on prior format: all file names are between | and |
                fileObjectList = []
                for names in attachmentsList:
                    fileObjectList.append(discord.File(names))      #must convert file-like objects to discord files before appending them to the file list
                responseFormatted = response.partition("|")         #remove the attachment tag before posting the reminder
            await message.channel.send(content=responseFormatted[0], files=fileObjectList)  #syntax for sending a message with both text and files
            reminp.close()

CLIENT = customClient()
CLIENT.run(TOKEN)                   #turn bot on -- buy the bot dinner prior to this step