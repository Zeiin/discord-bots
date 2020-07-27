import os, os.path
import discord
from discord import NotFound
import sys
import random
import re
import errno
from datetime import datetime
from dotenv import load_dotenv
from file_read_backwards import FileReadBackwards

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
        if(message.guild.name == gServerName):
            pattern = "(.*)(99!+)(.*)"
            prog = re.compile(pattern)
            result = prog.match(message.content)
            if result != None:
                with open(wordBankFile, encoding="utf8") as inp:        #always pass encoding in when opening a file, or else emojis and special chars fail and shit your text up
                    lines = inp.readlines()
                    random_line = random.randint(0, len(lines) - 1)     #ensures our random line is within proper bounds, no OOB tricks here speedrunners
                    response = lines[random_line]                       #pick a random line :)
                await message.channel.send(response)                    #sends the random line, all coroutines must be awaited? i think at least the ones I use do.

        UrlPattern = "((http|https)\:\/\/)?[a-zA-Z0-9\.\/\?\:@\-_=#]+\.([a-zA-Z]){2,6}([a-zA-Z0-9\.\&\/\?\:@\-_=#])*" #don't fucking ask
        UrlRegEx = re.compile(UrlPattern)
        UrlMatch = UrlRegEx.match(message.content)

        if len(message.attachments) > 0 or UrlMatch != None:
            await message.add_reaction('🔁')                         #retweet :)
            await message.add_reaction('❤')                         #like :)

        if message.content.lower().find("all my homies") != -1:
            await message.add_reaction('🔁')                         # retweet in solidarity with ur homie

        if message.content == "!cachereminders" or message.content == "!cacheimagines":                    #we cache reminders every so often instead of reading the entire message history every time we want to find a reminder
            curGUILD = message.guild                                #currentGuild to cache from

            targetGuildName = curGUILD.name.replace(" ", "").replace("\'","")
            if message.content == "!cachereminders":
                targetCacheFile = targetGuildName+ "/reminderCache.txt"
                targetCacheFile2 = targetGuildName+ "/reminderCache2.txt"
                targetCacheFile3 = targetGuildName+ "/reminderCache3.txt"
                targetWord="reminder"
                print(f'we chose to cache reminders \n')
            elif message.content == "!cacheimagines":
                targetCacheFile = targetGuildName + "/imagineCache.txt"
                targetCacheFile2 = targetGuildName + "/imagineCache2.txt"
                targetCacheFile3 = targetGuildName + "/imagineCache3.txt"
                targetWord="imagine"
                print(f'we chose to cache imagines \n')
            try:                                                    #EAFP principle in python, try to make the dir and if error aside from already exists occurs raise, otherwise ignore
                os.makedirs(targetGuildName + "/attachments")
            except OSError as e:
                if e.errno != errno.EEXIST:                         #Only raise exception if the error is NOT that the directory already exists
                    raise
            afterVal = None
            try:
                with open(targetCacheFile, "r") as dateCheck: #pull the most recent reminder (always the first reminder in file)
                    first_line = dateCheck.readline()
                    print(first_line)
                    afterValTemp = re.findall('\[\!\[(.*?)\[\!\[', first_line)                      #date format surrounded by [![ for a guarateed disambiguation
                    if(len(afterValTemp)>0):                                                        #if we got a valid date, should happen every time but who knows
                        afterVal = datetime.fromisoformat(afterValTemp[0])
                        print(f'LAST MESSAGE DATE RECORDED: {afterValTemp[0]}')
                    else:
                        afterVal = None
                if afterVal != None:                                                           # we now want our current file shoved elsewhere
                    os.rename(targetCacheFile,targetCacheFile2)                                 # so we can start writing our new reminders and add the old stuff under
                                                                                               #to maintain our first line = most recent reminder assumption
            except OSError as e:
                if e.errno != errno.ENOENT:
                    raise
            with open(targetCacheFile, encoding="utf8", mode="w") as outp: #keep reminder caches seperated by folders named after each server - special characters probably not handled here..
                for curCHANNEL in curGUILD.channels:
                    if curCHANNEL.type is discord.ChannelType.text: #only loop through text channels
                        print(f'{curCHANNEL.name} is of type {curCHANNEL.type}\n')
                        async for curMESSAGE in curCHANNEL.history(limit=None, after=afterVal): #for every message in this channel's history
                            if curMESSAGE.content.lower().find(targetWord) >= 0 and curMESSAGE.content.lower().find("!") != 0 and curMESSAGE.author != CLIENT.user:
                                curMESSAGEstripped = curMESSAGE.content.replace("\n", " ")
                                curVal = f'{curMESSAGE.author.mention} {curMESSAGEstripped} [![{curMESSAGE.created_at}[![' #Formats the beginning of the string to mention the user and post the reminder itself
                                for attachment in curMESSAGE.attachments:                     #check for files attached
                                    random.seed()                                             #random seed so duplicate file names almost never happen
                                    filName = f'{targetGuildName}/attachments/{random.randint(1,1000)}{attachment.filename}' #append random value to file name
                                    curVal += (f'|{filName}|+')                               #attaches a tag to the reminder line that indicates we have a file attachment
                                    await attachment.save(filName)                            #save the file-like object, must be converted to discord file on use
                                curVal += "\n"
                                outp.write(curVal)
                                print(curVal)
                    else:
                        print(f'{curCHANNEL.name} is of type {curCHANNEL.type}\n')
            if afterVal != None:
                if(os.stat(targetCacheFile).st_size > 0):
                    os.rename(targetCacheFile,targetCacheFile3)
                    with open(targetCacheFile, mode="a") as mostRecentReminders:
                        with FileReadBackwards(targetCacheFile3, encoding="utf-8") as reversedFile:
                            for reversedLines in reversedFile:
                                mostRecentReminders.write(reversedLines+"\n")
                    with open(targetCacheFile, mode="a") as combineFiles:
                        with open(targetCacheFile2) as sideFile:
                            for sideLine in sideFile:
                                combineFiles.write(sideLine)
                    os.remove(targetCacheFile2)
                    os.remove(targetCacheFile3)
                else:
                    os.remove(targetCacheFile)
                    os.rename(targetCacheFile2, targetCacheFile)
        """    with open(targetCacheFile, mode="r+") as afterChecker: #remove new line at the end
                afterChecker.seek(0, os.SEEK_END)                     # Move the pointer (similar to a cursor in a text editor) to the end of the file
                pos = afterChecker.tell() - 1                         # This code means the following code skips the very last character in the file -
                while pos > 0 and afterChecker.read(1) != "\n":       # Read each character in the file one at a time from the penultimate
                    pos -= 1
                    afterChecker.seek(pos, os.SEEK_SET)
                if pos > 0:                                           # So long as we're not at the start of the file, delete all the characters ahead
                    afterChecker.seek(pos, os.SEEK_SET)
                    afterChecker.truncate()                           #All this just to ensure we dont have a new line at the end of our file..
        """
        if message.content.find("!remind") == 0 or message.content.find("!imagine") ==0 :
            targetGuildName = message.guild.name.replace(" ", "").replace("\'","")
            if message.content.find("!remind") == 0:
                targetCacheFile =  f'{targetGuildName}/reminderCache.txt'
                targetWord = "remind"
            if message.content.find("!imagine") == 0:
                targetCacheFile = targetGuildName + "/imagineCache.txt"
                targetWord = "imagine"
            with open(targetCacheFile, encoding="utf8") as reminp:        #always pass encoding in when opening a file, or else emojis and special chars fail and shit your text up
                response = ""
                if(message.content.find("me") == -1):                     #filter by all messages or just ones made by author
                    while response == "" or response == "\n":
                        lines = reminp.readlines()
                        random_line = random.randint(0, len(lines) - 1)     #ensures our random line is within proper bounds, no OOB tricks here speedrunners
                        response = lines[random_line]                       #pick a random line :)
                else:
                    validMessages = []                                      #initialize list to append valid messages to
                    for allLines in reminp:
                        if allLines.find(message.author.mention) == 0:      #check if current line mentions same person that used command
                            validMessages.append(allLines)                  #if so, add to valid list
                    if len(validMessages) > 0:                              #only generate a response if the user has a valid message
                        response = random.choice(validMessages)
                    else:
                        response = f'{message.author.mention} Sorry, I could not find a valid message that includes the word **{targetWord}** to use for this command'
                attachmentsList = re.findall('\|(.*?)\|', response) #gets a list of all attachments possible, assumption based on prior format: all file names are between | and |
                fileObjectList = []
                for names in attachmentsList:
                    fileObjectList.append(discord.File(names))      #must convert file-like objects to discord files before appending them to the file list
                responseFormatted = response.partition("[![")         #remove the attachment tag before posting the reminder
            await message.channel.send(content=responseFormatted[0], files=fileObjectList)  #syntax for sending a message with both text and files

CLIENT = customClient()
CLIENT.run(TOKEN)                   #turn bot on -- buy the bot dinner prior to this step