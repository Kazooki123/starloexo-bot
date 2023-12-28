import discord
from discord.ext import commands

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='kick')
    async def kick_command(self, ctx, member: discord.Member, reason=None):
        # Kick command implementation

def setup(bot):
    bot.add_cog(Moderation(bot))
