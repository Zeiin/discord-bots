import os
import discord
import sys
import random
import re
from dotenv import load_dotenv

load_dotenv()                       #loads .env file in the same directory -- use for configs and any changes -- dont edit settings in this file, use the env file
TOKEN = os.getenv('DISCORD_TOKEN')  #loads PRIVATE discord token that we set as an env variable in the .env file -- this is done so you don't post private token to VCs software i.e github
gServerName = os.getenv('DISCORD_GUILD')  #guild is an object referencing the server the bot/users are in
AvatarFILE = os.getenv('AVATAR_PATH')
OriginalAvaterFILE = os.getenv("ORIGINAL_AVATAR_PATH")
#CLIENT = discord.Client()           #client is an object that handles all our interaction with discord -- events, state management, read/write, any api calls, etc.

class customClient(discord.Client):
    async def on_ready(self):              #api flags on_ready when the bot connects and all overhead is complete
        print(
            f'{CLIENT.user} is connected.'   #Confirming we online.
        )
    async def on_message(self, message):
        if message.author == CLIENT.user:
            return #--No self-loops

        print(f'{message.content}')
        if message.content.lower().find('crayon eater') > -1:
            await message.guild.me.edit(nick="Dmg04")
            with open(AvatarFILE, 'rb') as f:
                image = f.read()
            await self.user.edit(avatar=image)
            f.close()
            MentionAuth = message.author.mention
            DmgResponse = f"{MentionAuth} Crayon Eater is a Slur\n{MentionAuth} Crayon Eater is a SLUR\n{MentionAuth} CRAYON EATER IS A SLUR\n"
            await message.channel.send(DmgResponse)

        if message.content.lower().find('!resetd') > -1:
            await message.guild.me.edit(nick="Mystery")
            with open(OriginalAvaterFILE, 'rb') as f:
                image = f.read()
            await self.user.edit(avatar=image)
            f.close()
            await message.channel.send("The Mystery Returns.")

CLIENT = customClient()
CLIENT.run(TOKEN)                   #turn bot on -- buy the bot dinner prior to this step
