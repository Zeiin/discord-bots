import sys
import random
import re
import errno
import os, os.path
import discord
import logging
import boto3
import imageio
import PIL
from botocore.exceptions import ClientError
from PIL import Image
from datetime import datetime
from file_read_backwards import FileReadBackwards
PIL.Image.MAX_IMAGE_PIXELS = None


class Utilities:
    def pullRandomLine(self, fileNamei):
        with open(fileNamei, encoding="utf8", mode="r") as inp:
            random.seed()
            retVal = ""
            while retVal == "" or retVal == "\n":
                inpList = inp.readlines()
                random_inp = random.randint(0, len(
                    inpList) - 1)  # ensures our random line is within proper bounds, no OOB tricks here speedrunners
                retVal = inpList[random_inp]  # pick a random line :)
            retVal = retVal.replace("\n", "")
            return retVal

    def generateTownMessage(self, adjectiveFile, nounFile):
        adjectiveChoice = self.pullRandomLine(adjectiveFile)
        nounChoice = self.pullRandomLine(nounFile)
        generatedtown = f'How about {adjectiveChoice} {nounChoice}'
        return generatedtown

    def widenImage(self, imageFile, widenMultiple, noCrop = 0):
        im = Image.open(imageFile)
        oldWidth, oldHeight = im.size
        (width, height) = (im.width * 3 * widenMultiple, im.height // 1)  # Provide the target width and height of the image
        im = im.resize((width, height))
        if noCrop == 0 and width >= 2400 and height*2 < width:
            im = self.centerCrop(im, width/(3), height)
        im.save(imageFile)
        im.close()

    def centerCrop(self, img, desiredWidth, desiredHeight):
        curWidth, curHeight = img.size
        left, right = (curWidth - desiredWidth) / 2, (curWidth + desiredWidth) / 2
        top, bottom = (curHeight - desiredHeight) / 2, (curHeight + desiredHeight) / 2
        left, top = round(max(0, left)), round(max(0, top))
        right, bottom = round(min(curWidth - 0, right)), round(min(curHeight - 0, bottom))
        return img.crop((left, top, right, bottom))

    def analyseImage(self, im):
        '''
        Pre-process pass over the image to determine the mode (full or additive).
        Necessary as assessing single frames isn't reliable. Need to know the mode
        before processing all frames.
        '''
        results = {
            'size': im.size,
            'mode': 'full',
        }
        try:
            while True:
                if im.tile:
                    tile = im.tile[0]
                    update_region = tile[1]
                    update_region_dimensions = update_region[2:]
                    if update_region_dimensions != im.size:
                        results['mode'] = 'partial'
                        break
                im.seek(im.tell() + 1)
        except EOFError:
            pass
        im.seek(0)
        return results

    def getFrames(self, im):
        '''
        Iterate the GIF, extracting each frame.
        '''
        mode = self.analyseImage(im)['mode']

        p = im.getpalette()
        last_frame = im.convert('RGBA')

        try:
            while True:
                '''
                If the GIF uses local colour tables, each frame will have its own palette.
                If not, we need to apply the global palette to the new frame.
                '''
                if not im.getpalette():
                    im.putpalette(p)

                new_frame = Image.new('RGBA', im.size)

                '''
                Is this file a "partial"-mode GIF where frames update a region of a different size to the entire image?
                If so, we need to construct the new frame by pasting it on top of the preceding frames.
                '''
                if mode == 'partial':
                    new_frame.paste(last_frame)

                new_frame.paste(im, (0, 0), im.convert('RGBA'))
                yield new_frame

                last_frame = new_frame
                im.seek(im.tell() + 1)
        except EOFError:
            pass

    def processGifImage(self, path, widenMultiple, noCrop = 0):
        gifData = imageio.mimread(path, memtest=False)
        frameDelays = []
        frameData = []
        for metaData in gifData:
            frameDelays.append(metaData.meta["duration"] * .001)
            frameData.append(metaData)
        imageio.mimsave(path, frameData, fps=30, duration=frameDelays)
        im = Image.open(path)
        print(f'GIF OPENED BY PILLOW\n')
        frameList = []
        frameArr = []
        for (i,frame) in enumerate(self.getFrames(im)):
            #print("saving %s frame %d, %s %s" % (path, i, im.size, im.tile))
            oldWidth, oldHeight = frame.size
            (width, height) = (frame.width * 3 * widenMultiple, frame.height // 1)  # Provide the target width and height of the image
            frame = frame.resize((width, height))
            if noCrop == 0 and width >= 2400 and height * 2 < width:
                frame = self.centerCrop(frame, width / (3), height)
            frameList.append(frame)
            #frame.save('/resources/WidenGif/%s-%d.png' % (''.join(os.path.basename(path).split('.')[:-1]), i), 'PNG')
        #print(f'processed the frames? i guess?')
        frameList[0].save(path, save_all=True, append_images=frameList[1:], loop=0)
        im.close()
    # Normally this would be a simple for loop based on the arguments, but since the more common use case is going to be a single input
    # inclusive of spaces, I've set it up such that to do multiple inputs you must single quote, and for one long input inclusive of spaces you just type freely.
    def appendToFileWeirdly(self, ctx, fileName):
        with open(fileName, encoding="utf8", mode="a") as apndFile:
            quoteFinder = re.findall("\'(.*?)\'", ctx)
            if (len(quoteFinder) > 0):
                for val in quoteFinder:
                    if val != "":
                        val = val.replace("\'", "")
                        apndFile.write(f'\n{val}')
            elif ctx != "":
                apndFile.write(f'\n{ctx}')

    def pullFromCache(self, message, type):
        targetGuildName = message.guild.name.replace(" ", "").replace("\'", "")
        targetCacheFile = f'{targetGuildName}/{type}Cache.txt'
        if (message.content.find("me") == -1):  # filter by all messages or just ones made by author
            response = self.pullRandomLine(targetCacheFile)
        else:
            with open(targetCacheFile, encoding="utf8") as reminp:  # always pass encoding in when opening a file, or else emojis and special chars fail and shit your text up
                validMessages = []                                  # initialize list to append valid messages to
                for allLines in reminp:
                    if allLines.find(message.author.mention) == 0:  # check if current line mentions same person that used command
                        validMessages.append(allLines)              # if so, add to valid list
                if len(validMessages) > 0:                          # only generate a response if the user has a valid message
                    response = random.choice(validMessages)
                else:
                    response = f'{message.author.mention} Sorry, I could not find a valid message you\'ve sent that qualifies as a(n) **{type}** message'
        attachmentsList = re.findall('\|(.*?)\|', response)  # gets a list of all attachments possible, assumption based on prior format: all file names are between | and |
        fileObjectList = []
        for names in attachmentsList:
            fileObjectList.append(discord.File(names))  # must convert file-like objects to discord files before appending them to the file list
        responseFormatted = response
        responseFormatted = response.partition("[![")  # remove the attachment tag before posting the reminder
        #print(f'{responseFormatted[0]}, pulled from: {targetCacheFile}')
        return responseFormatted[0], fileObjectList

    async def populateCache(self, message, type):
        curGUILD = message.guild  # currentGuild to cache from
        targetGuildName = curGUILD.name.replace(" ", "").replace("\'", "")
        targetCacheFile =  f'{targetGuildName}/{type}Cache.txt'
        targetCacheFile2 = f'{targetGuildName}/{type}Cache2.txt'
        targetCacheFile3 = f'{targetGuildName}/{type}Cache3.txt'
        print(f'we chose to cache {type} from {targetGuildName} into {targetCacheFile}\n')
        try:                                            # EAFP principle in python, try to make the dir and if error aside from already exists occurs raise, otherwise ignore
            os.makedirs(targetGuildName + "/attachments")
        except OSError as e:
            if e.errno != errno.EEXIST:                 # Only raise exception if the error is NOT that the directory already exists
                raise

        afterVal = None
        try:
            with open(targetCacheFile,"r") as dateCheck:  # pull the most recent reminder (always the first reminder in file)
                first_line = dateCheck.readline()
                print(first_line)
                afterValTemp = re.findall('\[\!\[(.*?)\[\!\[',first_line)  # date format surrounded by [![ for a guarateed disambiguation
                if (len(afterValTemp) > 0):  # if we got a valid date, should happen every time but who knows
                    afterVal = datetime.fromisoformat(afterValTemp[0])
                    print(f'LAST MESSAGE DATE RECORDED: {afterValTemp[0]}')
                else:
                    afterVal = None
            if afterVal != None:                                # to maintain our first line = most recent reminder assumption, we now want our current file shoved elsewhere
                os.rename(targetCacheFile, targetCacheFile2)    # so we can start writing our new reminders and add the old stuff under
        except OSError as e:
            if e.errno != errno.ENOENT:
                raise
        print(f'OPENING CACHE FILE\n')
        with open(targetCacheFile, encoding="utf8", mode="w") as outp:  # keep reminder caches seperated by folders named after each server - special characters probably not handled here..
            for curCHANNEL in curGUILD.channels:
                if curCHANNEL.type is discord.ChannelType.text:  # only loop through text channels
                    print(f'{curCHANNEL.name} is of type {curCHANNEL.type}\n')
                    async for curMESSAGE in curCHANNEL.history(limit=None,after=afterVal):  # for every message in this channel's history
                        if curMESSAGE.content.lower().find(type) >= 0 and curMESSAGE.content.lower().find("!") != 0 and curMESSAGE.author != message.guild.me:
                            curMESSAGEstripped = curMESSAGE.content.replace("\n", " ")
                            print(f'{curMESSAGEstripped}\n')
                            curVal = f'{curMESSAGE.author.mention} {curMESSAGEstripped} [![{curMESSAGE.created_at}[!['  # Formats the beginning of the string to mention the user and post the reminder itself
                            for attachment in curMESSAGE.attachments:  # check for files attached
                                random.seed()  # random seed so duplicate file names almost never happen
                                filName = f'{targetGuildName}/attachments/{random.randint(1, 1000)}{attachment.filename}'  # append random value to file name
                                curVal += (f'|{filName}|+')  # attaches a tag to the reminder line that indicates we have a file attachment
                                await attachment.save(filName)  # save the file-like object, must be converted to discord file on use
                            curVal += "\n"
                            outp.write(curVal)
                            print(curVal)
                else:
                    print(f'{curCHANNEL.name} is of type {curCHANNEL.type}\n')
        if afterVal != None:
            if (os.stat(targetCacheFile).st_size > 0):
                os.rename(targetCacheFile, targetCacheFile3)
                with open(targetCacheFile, mode="a") as mostRecentReminders:
                    with FileReadBackwards(targetCacheFile3, encoding="utf-8") as reversedFile:
                        for reversedLines in reversedFile:
                            mostRecentReminders.write(reversedLines + "\n")
                with open(targetCacheFile, mode="a") as combineFiles:
                    with open(targetCacheFile2) as sideFile:
                        for sideLine in sideFile:
                            combineFiles.write(sideLine)
                os.remove(targetCacheFile2)
                os.remove(targetCacheFile3)
            else:
                os.remove(targetCacheFile)
                os.rename(targetCacheFile2, targetCacheFile)

    def upload_file(self, fileName, bucket, AWS_CLIENT, AWS_SECRET, CDN_DOMAIN, object_name=None):
        # If S3 object_name was not specified, use file_name
        if object_name is None:
            object_name = fileName.split('/')[-1]
        # Upload the file
        s3_client = client = boto3.client('s3', aws_access_key_id=AWS_CLIENT, aws_secret_access_key=AWS_SECRET)
        try:
            response = s3_client.upload_file(fileName, bucket, object_name, ExtraArgs={'ContentType': 'image/gif'})     #only doing this for gifs..
        except ClientError as e:
            logging.error(e)
            return None
        return f"{CDN_DOMAIN}{fileName.split('/')[-1]}"