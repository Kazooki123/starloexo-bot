import os
from dotenv import load_dotenv

import discord
from discord.ext import commands
from utils import image_search, jokes, quotes, wiki_search

# Load environment variables from .env file
load_dotenv()

client = commands.Bot(command_prefix='!')

# Define commands, using environment variables as needed
@client.command()
async def imgsearch(ctx, *, query):
    API_KEY = os.getenv("GOOGLE_CUSTOM_SEARCH_API_KEY")
    CX = os.getenv("GOOGLE_CUSTOM_SEARCH_ENGINE_ID")
    image_url = image_search(query, API_KEY, CX)  # Pass API keys as arguments
    # ... (rest of the command logic)

# ... (other commands, similarly accessing variables from .env as needed)

client.run(os.getenv("DISCORD_BOT_TOKEN"))  # Retrieve bot token from .env
