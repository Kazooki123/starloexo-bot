# In bot.py
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
import os
import requests
import io
from io import BytesIO
import random
import json
import asyncpg
import logging
from google_images_search import GoogleImagesSearch
import wikipediaapi
import asyncio
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from bardapi import BardAsync
import configparser

config = configparser.ConfigParser()
config.read('config.ini')
BARD_TOKEN = config["TOKENS"]['bard_token']
bard = BardAsync(token=BARD_TOKEN)

load_dotenv()

script_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(script_dir, 'emoji-quiz.json')

# Create a cache to store processed message IDs
# processed_messages = set()

logging.basicConfig(level=logging.DEBUG)

TOKEN = os.getenv('DISCORD_TOKEN')
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')

intents = discord.Intents.all()
intents.members = True
intents.message_content = True
intents.messages = True  # Enable message related events
intents.guilds = True    # Enable server-related events
intents.typing = True   # Enabled typing-related events for simplicity (optional)

bot = commands.Bot(command_prefix='!', intents=intents)

DATABASE_URL = os.getenv('POSTGRES_URL')

# Connect to PostgreSQL
async def create_pool():
    return await asyncpg.create_pool(DATABASE_URL)

# Load existing data when the bot starts
async def create_table():
    async with bot.pg_pool.acquire() as conn:
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS user_data (
                user_id bigint PRIMARY KEY,
                job text,
                wallet integer,
                experience integer,
                level integer
            )
            """
        )

# Load emoji quiz questions from the JSON file
with open(file_path, 'r', encoding='utf-8') as file:
    emoji_quiz_data = json.load(file)


@tasks.loop(minutes=30)  #30 for a 30-minute loop
async def send_emoji_quiz():
    # Replace with the ID of the channel where you want to send the emoji quiz
    channel_id = 1128638101854638112
    channel = bot.get_channel(channel_id)

    # Select a random emoji quiz question
    quiz_question = random.choice(emoji_quiz_data['questions'])
    emojis = quiz_question['emojis']
    correct_answer = quiz_question['answer'].lower()

    await channel.send(f"Guess the word represented by these emojis: {' '.join(emojis)}")


@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user.name}')
    bot.pg_pool = await create_pool()  # Move the pool creation inside the on_ready event
    await create_table()
    print("The bot is ready and the pg_pool attribute is created.")
    send_emoji_quiz.start()

async def load_extensions():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            await bot.load_extension(f"cogs.{filename[:-3]}")

@bot.command(name="reset")
async def reset(interaction: discord.Interaction):
    await interaction.response.defer()
    global bard
    bard = BardAsync(token=BARD_TOKEN)
    await interaction.followup.send("Chat context successfully reset.")
    return
    
@bot.command(name="chat")
async def chat(interaction: discord.Interaction, prompt: str, image: discord.Attachment = None):
    await interaction.response.defer()
    if image is not None:
        if not image.content_type.startswith('image/'):
            await interaction.response.send_message("File must be an image")
            return
        response = await bard.ask_about_image(prompt, await image.read())
        if len(response['content']) > 2000:
            embed = discord.Embed(title="Response", description=response['content'], color=0xf1c40f)
            await interaction.followup.send(embed=embed)
        else:
            await interaction.followup.send(response['content'])
            return
    response = await generate_response(prompt) 
    if len(response['content']) > 2000:
        embed = discord.Embed(title="Response", description=response['content'], color=0xf1c40f)
        await interaction.followup.send(embed=embed)
    else:
        await interaction.followup.send(response['content'])
    return

async def generate_response(prompt):
    response = await bard.get_answer(prompt)
    if not "Unable to get response." in response["content"]:
        config = read_config()
        if config.getboolean("SETTINGS", "use_images"):
            images = response["images"]
            if images:
                for image in images:
                    response["content"] += f"\n{image}"
        return response

@bot.command(name="public")
async def public(interaction: discord.Interaction):
    config = read_config()
    if config.getboolean("SETTINGS", "reply_all"):
        await interaction.response.send_message("Bot is already in public mode")
    else:
        config["SETTINGS"]["reply_all"] = "True"
        await interaction.response.send_message("Bot will now respond to all messages")
    write_config(config)
    return

@bot.command(name="private")
async def private(interaction: discord.Interaction):
    config = read_config()
    if not config.getboolean("SETTINGS", "reply_all"):
        config["SETTINGS"]["reply_all"] = "false"
        await interaction.response.send_message("Bot will now only respond to !chat")
    else:
        await interaction.response.send_message("Bot is already in private mode")
    write_config(config)
    return


# @bot.event
# async def on_message(message):
    # config = read_config()
    # if config.getboolean("SETTINGS", "reply_all"):
        # if message.author == bot.user:
            # return
        # async with message.channel.typing():
            # response = await generate_response(message.content)
            # if len(response['content']) > 2000:
                # embed = discord.Embed(title="Response", description=response['content'], color=0xf1c40f)
                # await message.channel.send(embed=embed)
            # else:
                # await message.channel.send(response['content'])
    
def read_config():
    config = configparser.ConfigParser()
    config.read("config.ini")
    return config

def write_config(config):
    with open("config.ini", "w") as configfile:
        config.write(configfile)

# Listen to the on_message event
# @bot.event
# async def on_message(message):
    # Ignore messages from bots
    # if message.author.bot:
        # return
    # Update the user data
    # await ranks.update_user_data(message.author, message, bot) # Use the update_user_data function from ranks module
    # Process any commands
    # await bot.process_commands(message)

# Command to fetch jokes
@bot.command(name='jokes')
async def jokes(ctx):
    try:
        # Fetch a random joke from JokeAPI
        response = requests.get('https://v2.jokeapi.dev/joke/Programming,Miscellaneous,Pun,Spooky,Christmas?blacklistFlags=nsfw,religious,political,racist,sexist')
        response.raise_for_status()  # Raise an HTTPError for bad responses
        data = response.json()

        # Check if it's a two-part joke or a single-part joke
        if 'delivery' in data:
            await ctx.send(f"{ctx.author.mention}, here's a joke for you:\n{data['setup']}\n{data['delivery']}")
        else:
            await ctx.send(f"{ctx.author.mention}, here's a joke for you:\n{data['joke']}")
    except Exception as e:
        print(f"Error in !jokes command: {e}")
        await ctx.send("An error occurred while processing the command.")

# Command to convert YouTube link to video file using YouTube API
@bot.command(name='convert')
async def convert(ctx, video_url):
    try:
        # Extract video ID from the URL
        if 'youtu.be' in video_url:
            video_id = video_url.split('/')[-1]
        else:
            video_id = video_url.split('v=')[1].split('&')[0]

        # Check if the video_id is not empty
        if not video_id:
            raise IndexError("Video ID not found in the URL")

        # Build the YouTube API service
        youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

        # Get video details using the YouTube API
        video_details = youtube.videos().list(part='snippet', id=video_id).execute()
        video_title = video_details['items'][0]['snippet']['title']

        # Send the video title as a message
        await ctx.send(f'Converting video: {video_title}')

        # Send the YouTube link as an attachment to the Discord channel
        await ctx.send(f'{ctx.author.mention}, here is the video:', file=discord.File(BytesIO(video_url.encode()), filename=f'{video_title}.mp4'))

    except HttpError as e:
        print(f'YouTube API Error: {e}')
        await ctx.send('Error converting the YouTube video. Please check the URL and try again.')
    except IndexError as e:
        print(f'Error extracting video ID from URL: {e}')
        await ctx.send('Error extracting the video ID from the URL. Please check the URL format.')

# Quotes command
@bot.command(name='quotes')
async def quotes(ctx):
    response = requests.get('https://api.quotable.io/random')
    data = response.json()
    quote = f"{data['content']} - {data['author']}"
    await ctx.send(quote)

# Command to perform image search
@bot.command(name='imgsearch')
async def imgsearch(ctx, *, query):
    google_api_key = os.getenv('GOOGLE_API_KEY')
    google_cx = os.getenv('GOOGLE_CX')

    if not google_api_key or not google_cx:
        await ctx.send('Google API key or CX not provided.')
        return

    gis = GoogleImagesSearch(google_api_key, google_cx)
    _search_params = {
        'q': query,
        'num': 4,  # Fetch four images
        'safe': 'high',
        'fileType': 'png|jpg',
    }

    gis.search(search_params=_search_params)

    try:
        # Accumulate image URLs
        image_urls = [result.url for result in gis.results()]

        # Send all images in a single message
        await ctx.send(f"{ctx.author.mention}, here are the images for you:", files=[discord.File(io.BytesIO(requests.get(url).content), f'image{i}.png') for i, url in enumerate(image_urls)])
    except Exception as e:
        print(f"Error in !imgsearch command: {e}")
        await ctx.send("An error occurred while processing the command.")


@bot.command(name='hangman')
async def hangman(ctx):
    word_to_guess = "discord"  # Replace with your word selection logic
    guessed_word = ['_'] * len(word_to_guess)
    attempts_left = 6

    while attempts_left > 0 and '_' in guessed_word:
        await ctx.send(f"{' '.join(guessed_word)}\nAttempts left: {attempts_left}")
        guess = await bot.wait_for('message', check=lambda m: m.author == ctx.author and m.channel == ctx.channel)
        guess = guess.content.lower()

        if guess in word_to_guess:
            for i, letter in enumerate(word_to_guess):
                if letter == guess:
                    guessed_word[i] = guess
        else:
            attempts_left -= 1

    if '_' not in guessed_word:
        await ctx.send(f"Congratulations! You guessed the word: {''.join(guessed_word)}")
    else:
        await ctx.send(f"Sorry, you ran out of attempts. The word was: {word_to_guess}")


@bot.command(name='emoji-quiz')
async def emoji_quiz(ctx):
    # Select a random emoji quiz question
    quiz_question = random.choice(emoji_quiz_data['questions'])
    emojis = quiz_question['emojis']
    correct_answer = quiz_question['answer'].lower()

    await ctx.send(f"Guess the word represented by these emojis: {' '.join(emojis)}")

    def check(message):
        return message.author == ctx.author and message.channel == ctx.channel

    try:
        guess = await bot.wait_for('message', check=check, timeout=30.0)
    except asyncio.TimeoutError:
        await ctx.send("Time's up! The correct answer was: {correct_answer}")
        return

    guess = guess.content.lower()

    if guess == correct_answer:
        await ctx.send("Congratulations! You guessed correctly.")
    else:
        await ctx.send(f"Sorry, the correct answer was: {correct_answer}")

# Wikipedia Search command
@bot.command(name='wiki')
async def wiki(ctx, *, query):
    try:
        headers = {'User-Agent': 'StarloExo Bot/1.0 (Discord Bot)'}
        wiki_wiki = wikipediaapi.Wikipedia('en', headers=headers)
        page_py = wiki_wiki.page(query)

        if page_py.exists():
            summary = page_py.summary
            # Split the summary into chunks of 2000 characters
            chunks = [summary[i:i+2000] for i in range(0, len(summary), 2000)]

            for chunk in chunks:
                await ctx.send(f'**{page_py.title}**: {chunk}')
        else:
            await ctx.send('Page not found.')
    except Exception as e:
        print(f"Error in !wiki command: {e}")
        await ctx.send("An error occurred while processing the command.")

# Command to apply for a job
@bot.command(name='apply')
async def apply(ctx):
    jobs = ["Engineer", "Programmer", "Artist"]
    job_message = "\n".join([f"{i+1}. {job}" for i, job in enumerate(jobs)])

    await ctx.send(f"{ctx.author.mention}, choose a job by replying with the corresponding number:\n{job_message}")

    def check(message):
        return message.author == ctx.author and message.channel == ctx.channel

    try:
        reply = await bot.wait_for('message', check=check, timeout=30)
        job_number = int(reply.content)

        if 1 <= job_number <= len(jobs):
            job = jobs[job_number - 1]

            async with bot.pg_pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO user_data (user_id, job, wallet)
                    VALUES ($1, $2, $3)
                    ON CONFLICT (user_id) DO NOTHING
                    """,
                    ctx.author.id, job, 0
                )

            await ctx.send(f"{ctx.author.mention}, applied as {job}.")
        else:
            await ctx.send(f"{ctx.author.mention}, invalid job number.")
    except asyncio.TimeoutError:
        await ctx.send(f"{ctx.author.mention}, timeout. Please use !apply again.")

# Command to work
@bot.command(name='work')
async def work(ctx):
    async with bot.pg_pool.acquire() as conn:
        user_data = await conn.fetchrow(
            "SELECT job, wallet FROM user_data WHERE user_id = $1",
            ctx.author.id
        )

    if user_data:
        job, _ = user_data
        earnings = random.randint(1, 90000)  # Simulate random earnings

        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE user_data
                SET wallet = wallet + $1
                WHERE user_id = $2
                """,
                earnings, ctx.author.id
            )

        await ctx.send(f"{ctx.author.mention}, you worked as a {job} and earned {earnings} coins.")
    else:
        await ctx.send(f"{ctx.author.mention}, you need to !apply for a job first.")

# Command to check wallet
@bot.command(name='wallet')
async def wallet(ctx):
    async with bot.pg_pool.acquire() as conn:
        wallet_amount = await conn.fetchval(
            "SELECT wallet FROM user_data WHERE user_id = $1",
            ctx.author.id
        )

    if wallet_amount is not None:
        await ctx.send(f"{ctx.author.mention}, your wallet balance is {wallet_amount} coins 🪙🪙.")
    else:
        await ctx.send(f"{ctx.author.mention}, you need to !apply for a job first.")

# Start the bot
bot.run(TOKEN)
