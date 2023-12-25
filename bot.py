import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import requests
import io
import logging
from google_images_search import GoogleImagesSearch
import wikipediaapi

load_dotenv()

logging.basicConfig(level=logging.DEBUG)

TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.all()
intents.message_content = True
intents.messages = True  # Enable message related events
intents.guilds = True    # Enable server-related events
intents.typing = True   # Enabled typing-related events for simplicity (optional)

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user.name}')

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
        'num': 1,
        'safe': 'high',
        'fileType': 'png|jpg',
    }

    gis.search(search_params=_search_params)
    result = gis.results()[0]

    try:
        # Download the image
        image_content = requests.get(result.url).content

        # Send the image as a file
        await ctx.send(f"{ctx.author.mention}, here's the image you requested:", file=discord.File(io.BytesIO(image_content), 'image.png'))
    except Exception as e:
        print(f"Error in !imgsearch command: {e}")
        await ctx.send("An error occurred while processing the command.")

# Wikipedia Search command
@bot.command(name='wiki')
async def wiki(ctx, *, query):
    wiki_wiki = wikipediaapi.Wikipedia('en')
    page_py = wiki_wiki.page(query)
    if page_py.exists():
        summary = page_py.summary[:2000]
        await ctx.send(f'**{page_py.title}**: {summary}...')
    else:
        await ctx.send('Page not found.')

# Other commands can be added here

# Start the bot
bot.run(TOKEN)
