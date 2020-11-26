import discord
import asyncio
import random
from discord.ext import commands, tasks
import os
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from PIL import Image, ImageEnhance, ImageFont, ImageDraw
from io import BytesIO
import textwrap

intents = discord.Intents(messages=True, guilds=True, reactions=True, members=True, presences=True, voice_states=True)
client = commands.Bot(command_prefix='$', intents=intents)
client.target = {}
game_list = {}
morning_channel = {}
voice = {}
nsfw = {}
stop_words = set(stopwords.words('english'))


def getmp3s(path):
    mp3_list = []
    if not os.path.isdir(path):
        print("File not found")
        return

    for file in os.listdir(path):
        if file.endswith(".mp3"):
            mp3_list.append(file)
    return mp3_list


def remove_noise_words(word):
    numbers = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, "i", "ii", "iii", "iv", "v", "vi", "vii", "viii", "ix", "x", "xi", "xii",
               "xiv", "xv",
               "xvi", "xvii", "xviii", "xix", "xx"]
    word_tokens = word_tokenize(word)
    filtered_sentence = [w for w in word_tokens if w not in stop_words and w not in numbers]
    return " ".join(filtered_sentence)


def draw_multiple_line_text(image, text, font, text_color, text_start_height):
    draw = ImageDraw.Draw(image)
    image_width, image_height = image.size
    y_text = text_start_height
    lines = textwrap.wrap(text, width=40)
    for line in lines:
        line_width, line_height = font.getsize(line)
        draw.text(((image_width + line_width) / 2, y_text), line, font=font, fill=text_color)
        y_text += line_height


def draw_multiple_line_stroke_text(image, text, font, text_color, text_start_height):
    draw = ImageDraw.Draw(image)
    image_width, image_height = image.size
    y_text = text_start_height
    scalar = image_width if image_width > image_height else image_height
    shrinker = len(text) if scalar > 800 else 0
    wrap_limit = int(abs((scalar - (font.size * 1.333333333)) ** (1 / 2) + shrinker))
    lines = textwrap.wrap(text, width=wrap_limit)
    for line in lines:
        line_width, line_height = font.getsize(line)
        draw.text(((image_width - line_width) / 2, y_text), line, font=font, fill=text_color, stroke_width=int(font.size/10),
                  stroke_fill=(0, 0, 0))
        y_text += line_height


def in_channel(guild: discord.Guild):
    if voice.get(guild) is None:
        return False
    if not voice.get(guild).is_connected():
        return False
    return True


insult_list = getmp3s('insults')
lonely_list = getmp3s('alone')


@client.event
async def on_ready():
    await client.change_presence(activity=discord.Game(name='Driving with Vito'))
    print("Joe is up and running")


@client.event
async def on_member_update(before, after):
    global game_list
    activity_type = None
    try:
        activity_type = after.activity.type
    except:
        return

    if activity_type is discord.ActivityType.playing and after == client.target.get(after.guild):
        if game_list.get(after.guild) is None or not game_list.get(after.guild).__contains__(
                remove_noise_words(after.activity.name.lower())):
            if game_list.get(after.guild) is None:
                temp = [remove_noise_words(after.activity.name.lower())]
                game_list[after.guild] = temp
                return
            game_list.get(after.guild).append(remove_noise_words(after.activity.name.lower()))


@tasks.loop(hours=24)
async def morning(guild: discord.Guild):
    global morning_channel
    await morning_channel.get(guild).send(f"Good Morning {guild.name}")
    if client.target.get(guild) is not None:
        responses = ["I hope you shit yourself", "I hope you have a terrible day",
                     "You're fat", "You're ugly"]
        await morning_channel.get(guild).send(f"except you {client.target.get(guild).display_name}")
        await asyncio.sleep(2)
        await morning_channel.get(guild).send(random.choice(responses))


@client.event
async def on_voice_state_update(member, before, after):
    global voice
    if after.self_stream and member == client.target.get(member.guild):
        if in_channel(member.guild):
            return
        channel = member.voice.channel
        voice[member.guild] = await channel.connect()
        while after.self_stream:
            audio_source = discord.FFmpegOpusAudio('insults/' + random.choice(insult_list))
            wait = random.randint(20, 60)
            await asyncio.sleep(wait)
            voice.get(member.guild).play(audio_source)
            voice.get(member.guild).source.volume = 0.08
        await voice.get(member.guild).disconnect()
    if after.channel is not None and not member.bot:
        if len(after.channel.members) == 1 and not in_channel(member.guild):
            audio_source = discord.FFmpegOpusAudio('alone/' + random.choice(lonely_list))
            await asyncio.sleep(4)
            if len(after.channel.members) == 1 and not in_channel(member.guild):
                voice[member.guild] = await member.voice.channel.connect()
                voice.get(member.guild).play(audio_source)
                voice.get(member.guild).source.volume = 0.07
                await asyncio.sleep(3)
                await voice.get(member.guild).disconnect()
                return
    if before.channel is not None and after.channel is not before.channel and not member.bot:
        if len(before.channel.members) == 1 and not in_channel(member.guild):
            audio_source = discord.FFmpegOpusAudio('alone/' + random.choice(lonely_list))
            await asyncio.sleep(4)
            if len(before.channel.members) == 1 and not in_channel(member.guild):
                voice[member.guild] = await before.channel.connect()
                voice.get(member.guild).play(audio_source)
                voice.get(member.guild).source.volume = 0.07
                await asyncio.sleep(3)
                await voice.get(member.guild).disconnect()
                return


@client.event
async def on_message(message):
    await client.process_commands(message)
    if not str(message.content).lower().find('joe') == -1 and not str(message.content).lower().find('fuck') == -1:
        choice = random.randint(0, 1)
        if choice == 0:
            ugly = Image.open("picture/ugly.jpg")
            asset = message.author.avatar_url_as(size=128)
            data = BytesIO(await asset.read())
            pfp = Image.open(data)
            pfp = pfp.resize((157, 136))
            ugly.paste(pfp, (341, 122))
            ugly.save("uggo.jpg")
            await message.channel.send("I drew a picture of you, why don't you fuck that")
            await message.channel.send(file=discord.File("uggo.jpg"))
            os.remove("uggo.jpg")
        if choice == 1:
            responses = ["That's an unprofessional way of addressing your superior my friend",
                         "If I weren't trapped in this digital hell I'd give ya a shiner",
                         f"Fuck me? why don't you go fuck {random.choice(message.guild.members).display_name} instead"]
            await message.channel.send(random.choice(responses))
    if message.author == client.target.get(message.author.guild) and game_list.get(message.guild) is not None:
        for game in game_list.get(message.guild):
            prompt = str(message.content).lower()
            parts = str(game).split()
            for word in parts:
                if not prompt.find(word) == -1:
                    responses = [
                        f"Hey why don't you take {game} and shove it up your ass, {client.target.get(message.author.guild).display_name}",
                        f"Playing all that {game} will rot your brains, pal",
                        f"Quit yappin' about {game}, {client.target.get(message.author.guild).display_name}",
                        f"At this rate, you'll die alone playing all that {game}, {client.target.get(message.author.guild).display_name}"]
                    channel = message.channel
                    await channel.send(random.choice(responses))
                    return


@client.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Please pass in all required arguments")
    if isinstance(error, commands.MemberNotFound):
        await ctx.send("either you didn't mention ths guy or he doesn't exist")


@client.command(name="insult", help="joins your channel and plays an insult sound")
async def insult(ctx):
    audio_source = discord.FFmpegOpusAudio('insults/' + random.choice(insult_list))
    global voice
    if not ctx.message.author.voice:
        await ctx.send('Join a voice channel bozo')
        return
    if in_channel(ctx.guild):
        await ctx.send("I'm busy")
        return
    channel = ctx.message.author.voice.channel
    voice[ctx.guild] = await channel.connect()
    voice.get(ctx.guild).play(audio_source)
    voice.get(ctx.guild).source.volume = 0.07
    await asyncio.sleep(7)
    await voice.get(ctx.guild).disconnect()


@client.command(name="target", help="selects who Joe will bully, the target can't use this command")
async def target(ctx, user: discord.Member):
    if ctx.message.author == client.target.get(ctx.guild) or not ctx.message.author.guild_permissions.move_members:
        await ctx.send("I don't take orders from the likes of you")
        return
    client.target[ctx.guild] = user
    await ctx.send(f'prepare yourself {user.mention}')


@client.command(name="getTarget", help="gets the current target")
async def getTarget(ctx):
    if client.target.get(ctx.guild) is None:
        await ctx.send("I'm not targeting anyone, use $target <mention> to pick a victim")
        return
    await ctx.send(f"I am lowering {client.target.get(ctx.guild).display_name}'s self esteem")


@client.command()
async def leave(ctx):
    if ctx.message.author == client.target.get(ctx.guild) or not ctx.message.author.guild_permissions.move_members:
        await ctx.send("I don't take orders from the likes of you")
        return
    global voice
    if in_channel(ctx.guild):
        await voice.get(ctx.guild).disconnect()


@client.command(name="deepfry", help="deep frys the image sent in the previous message")
async def deepfry(ctx):
    messages = await ctx.message.channel.history(limit=2).flatten()
    if len(messages[1].attachments) > 0:
        items = messages[1].attachments
        for image in items:
            if image.url.endswith(".jpg") or image.url.endswith(".png") or image.url.endswith(".jpeg"):
                data = BytesIO(await image.read())
                pic = Image.open(data)
                pic_con = ImageEnhance.Contrast(pic).enhance(8)
                pic_fin = ImageEnhance.Sharpness(pic_con).enhance(8)
                pic_fin.save("garbage.png")
                await ctx.send("Congrats it looks even more like shit now")
                await ctx.send(file=discord.File("garbage.png"))
                os.remove("garbage.png")


@client.command(name="plow", help="go ahead, mention two people nsfw channel only by default")
async def plow(ctx, plowee: discord.Member = None, plower: discord.Member = None):
    global nsfw
    if not ctx.channel.is_nsfw():
        if nsfw.get(ctx.guild) is None or nsfw.get(ctx.guild) == True:
            await ctx.send("use in a nsfw channel or, if you are an administrator use $toggleNsfw")
            return
    if plowee is None:
        plowee = ctx.message.author
    if plower is None:
        plower = client.user
    pic = Image.open("picture/plow.jpg")
    asset1 = plowee.avatar_url_as(size=128)
    asset2 = plower.avatar_url_as(size=128)
    data1 = BytesIO(await asset1.read())
    data2 = BytesIO(await asset2.read())
    pfp_b = Image.open(data1)
    pfp_a = Image.open(data2)
    pfp_b = pfp_b.resize((187, 184))
    pfp_a = pfp_a.resize((150, 145))
    pic.paste(pfp_a, (604, 80))
    pic.paste(pfp_b, (105, 356))
    pic.save("bad.jpg")
    await ctx.send("I'm like a modern day picasso")
    await ctx.send(file=discord.File("bad.jpg"))
    os.remove("bad.jpg")


@client.command(name="ouch", help="kick your pals in the nads!")
async def ouch(ctx, victim: discord.Member = None, perp: discord.Member = None):
    if victim is None or type(victim) is not discord.Member:
        victim = ctx.message.author
    if perp is None:
        perp = client.user
    pic = Image.open("picture/ouch.jpg")
    asset1 = victim.avatar_url_as(size=128)
    asset2 = perp.avatar_url_as(size=128)
    data1 = BytesIO(await asset1.read())
    data2 = BytesIO(await asset2.read())
    pfp_b = Image.open(data1)
    pfp_a = Image.open(data2)
    pfp_b = pfp_b.resize((210, 184))
    pfp_a = pfp_a.resize((178, 165))
    pic.paste(pfp_a, (129, 96))
    pic.paste(pfp_b, (440, 70))
    pic.save("oof.jpg")
    await ctx.send("I don't usually look at these kinds a pictures,but-")
    await ctx.send(file=discord.File("oof.jpg"))
    os.remove("oof.jpg")


@client.command(name="tweet", help="makes a fake tweet")
async def tweet(ctx, victim: discord.Member, *, message=None):
    responses = [f"I can't believe {victim.display_name} said that", "A real potty mouth on this one",
                 f"I don't think I like this {victim.display_name} guy anymore", "Get a load of this idiot",
                 f"Do you kiss your mother with that mouth {victim.display_name}"]
    if message is None:
        message = "Hey idiot the syntax was $tweet <mention> <message>"
    template = Image.open("picture/tweet.png")
    font = ImageFont.truetype("arial.ttf", 18)
    asset = victim.avatar_url_as(size=128)
    data = BytesIO(await asset.read())
    pfp = Image.open(data)
    pfp = pfp.resize((33, 32))
    template.paste(pfp, (7, 13))
    draw_multiple_line_text(template, message, font, (0, 0, 0), 61)
    draw = ImageDraw.Draw(template)
    draw.text((50, 22), victim.display_name, (0, 0, 0), font=font)
    template.save("twit.png")
    await ctx.send(random.choice(responses))
    await ctx.send(file=discord.File("twit.png"))
    os.remove("twit.png")


@client.command(name="goodMorning", help="sets this channel for good morning messages")
async def goodMorning(ctx):
    morning_channel[ctx.guild] = ctx.channel
    morning.start(ctx.guild)


@client.command(name="toggleNsfw", help="toggles the nsfw restriction on the plow command")
async def toggleNsfw(ctx):
    global nsfw
    if not ctx.message.author.guild_permissions.administrator:
        await ctx.send("sorry pal, admin only")
        return
    else:
        if nsfw.get(ctx.guild) is None:
            nsfw[ctx.guild] = False
            await ctx.send(f"the nsfw restriction is now {nsfw.get(ctx.guild)}")
            return
        nsfw[ctx.guild] = not nsfw.get(ctx.guild)
        await ctx.send(f"the nsfw restriction is now {nsfw.get(ctx.guild)}")
        return


@client.command(name="bottomText", help="adds bottom text to previous image")
async def bottomText(ctx, *, message):
    messages = await ctx.message.channel.history(limit=2).flatten()
    if len(messages[1].attachments) > 0:
        items = messages[1].attachments
        for image in items:
            if image.url.endswith(".jpg") or image.url.endswith(".png") or image.url.endswith(".jpeg"):
                data = BytesIO(await image.read())
                pic = Image.open(data)
                width, height = pic.size
                scalar = int(height) if height < width else int(width)
                shrinker = len(message) if scalar > 250 else 0
                font = ImageFont.truetype("impact.ttf", int(abs((scalar / len(message)) + shrinker)))
                draw_multiple_line_stroke_text(pic, message, font, (255, 255, 255), pic.height - (height / 4))
                pic.save("funni.png")
                await ctx.send(file=discord.File("funni.png"))
                os.remove("funni.png")
                return


client.run('Nzc2NjQ2MDkzNTIxMDI3MTAy.X636Cg.GrdtV0KKR8Fs5AeUDxaUbtj6U-E')
