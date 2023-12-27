import os

from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

WELCOME_CHANNEL_ID = os.getenv('WELCOME_CHANNEL_ID')

class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        print(f"Member {member} joined the server.")
        # Customize the welcome message with the member's name and server name
        welcome_message = f"Welcome {member.name} to {member.guild.name} server! We're glad to have you."

        # Send the welcome message to a specific channel (replace CHANNEL_ID with the actual channel ID)
        channel = member.guild.get_channel(WELCOME_CHANNEL_ID)
        await channel.send(welcome_message)

def setup(bot):
    bot.add_cog(Welcome(bot))
