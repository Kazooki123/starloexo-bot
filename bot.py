# In bot.py
import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import requests
import io
import random
import asyncpg
import logging
from google_images_search import GoogleImagesSearch
import wikipediaapi
import asyncio

load_dotenv()

# Create a cache to store processed message IDs
# processed_messages = set()

logging.basicConfig(level=logging.DEBUG)

TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.all()
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

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user.name}')
    bot.pg_pool = await create_pool()  # Move the pool creation inside the on_ready event
    await create_table()
    print("The bot is ready and the pg_pool attribute is created.") # Add this line to check if the on_ready event is triggered

# Load the ranks.py module as an extension
async def load_extensions():
    # Load the ranks extension
    await bot.load_extension("ranks")
    # Load any other extensions you want

asyncio.run(load_extensions())

# Listen to the on_message event
@bot.event
async def on_message(message):
    # Ignore messages from bots
    if message.author.bot:
        return
    # Update the user data
    await ranks.update_user_data(message.author, message, bot) # Use the update_user_data function from ranks module
    # Process any commands
    await bot.process_commands(message)

# Command to fetch jokes
@bot.command(name='jokes')
async def jokes(ctx):
    try:
        # Fetch a random joke from JokeAPI
        response = requests.get('https://v2.jokeapi.dev/joke/Any')
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
        earnings = random.randint(1, 10)  # Simulate random earnings

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
        await ctx.send(f"{ctx.author.mention}, your wallet balance is {wallet_amount} coins.")
    else:
        await ctx.send(f"{ctx.author.mention}, you need to !apply for a job first.")

# Start the bot
bot.run(TOKEN)
