import os
import discord
import sys
import random
import re
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
        if (GUILD == None):                # .find returns "None" if no matching value is found. In this case the bot has no purpose so it should exit.
            print(
                f'GUILD NOT FOUND -- EXITING'
            )
            sys.exit(1)
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

        if len(message.attachments) > 0:
            await message.add_reaction('🔁')                         #retweet :)


CLIENT = customClient()
CLIENT.run(TOKEN)                   #turn bot on -- buy the bot dinner prior to this step