import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import requests
import logging
from google_images_search import GoogleImagesSearch
import wikipediaapi

load_dotenv()

logging.basicConfig(level=logging.DEBUG)

TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.messages = True  # Enable message related events
intents.guilds = True    # Enable server-related events
intents.typing = False   # Disable typing-related events for simplicity (optional)

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user.name}')

# Jokes command
@bot.command(name='memes')
async def memes(ctx):
    try:
        response = requests.get('https://meme-api.herokuapp.com/gimme')
        data = response.json()
        await ctx.send(data['url'])
    except Exception as e:
        print(f"Error in !memes command: {e}")
        await ctx.send("An error occurred while processing the command.")

# Quotes command
@bot.command(name='quotes')
async def quotes(ctx):
    response = requests.get('https://api.quotable.io/random')
    data = response.json()
    quote = f"{data['content']} - {data['author']}"
    await ctx.send(quote)

# Image Search command
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
    await ctx.send(result.url)

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
