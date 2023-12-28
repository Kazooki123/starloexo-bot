import os
import discord
from discord.ext import commands

WELCOME_CHANNEL_ID = int(os.getenv('WELCOME_CHANNEL_ID'))

class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        channel = member.guild.get_channel(WELCOME_CHANNEL_ID)
        welcome_message = f"Welcome {member.name} to {member.guild.name} server! We're glad to have you."
        await channel.send(welcome_message)

    @commands.command(name='welcome')
    async def set_welcome_channel(self, ctx, channel: discord.TextChannel):
        print(f"Welcome channel set to: {channel.id}")
        await ctx.send(f"Welcome channel set to: {channel.mention}")

def setup(bot):
    bot.add_cog(Welcome(bot))
