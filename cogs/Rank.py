from discord.ext import commands, tasks
from discord.ext.commands import cog_check
from sqlalchemy import create_engine, Column, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import discord
import random
import os
from asyncio import Queue, sleep

# Define the database connection string
DATABASE_URL = os.getenv('DATABASE_URL')  # Replace with your PostgreSQL connection string
engine = create_engine(DATABASE_URL)

# Define the base class for the SQLAlchemy model
Base = declarative_base()

# Define the User model
class User(Base):
    __tablename__ = 'user_data'

    user_id = Column(Integer, primary_key=True)
    level = Column(Integer, default=0)
    experience = Column(Integer, default=0)

# Create the table if it doesn't exist
Base.metadata.create_all(engine)

# Create a session to interact with the database
Session = sessionmaker(bind=engine)

# Define the formula to calculate the level from the experience
def level_formula(experience):
    return int(experience ** 0.25)

class Rank(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.message_queue = Queue()

        # Start the loop
        self.update_user_data.start()

    # Define a function to update the user data
    @tasks.loop(seconds=1000)
    async def update_user_data(user, self):
        """Update the user's level and experience based on their messages.

        Args:
            user (discord.Member): The user who sent the message.
            message (discord.Message): The message that the user sent.
            bot (commands.Bot): The bot object.
        """
        # Create a session to interact with the database
        session = Session()

        # Check if the user is already in the data
        user_data = session.query(User).get(user.id)
        if user_data is None:
            # If not, create a new entry with default values
            user_data = User(user_id=user.id, level=0, experience=0)
            session.add(user_data)

        # Increment the user's experience by a random amount between 5 and 10
        user_data.experience += random.randint(5, 10)

        # Calculate the user's level based on their experience
        level = level_formula(user_data.experience)

        # Check if the user has leveled up
        if level > user_data.level:
            # If yes, update their level and send a message
            user_data.level = level
            session.commit()
            # Send the message to the queue
            await self.message_queue.put(f"Congrats {user.mention}! You reached level {level} 🥳")

        # Close the session
        session.close()
    
    async def send_messages(self):
        """Send messages from the queue."""
        while True:
            message = await self.message_queue.get()
            # Replace CHANNEL_ID with the actual channel ID
            channel = self.bot.get_channel(1189735477222322217)
            await channel.send(message)
            # Sleep for a short duration to avoid potential rate limits
            await sleep(1)

    def cog_unload(self):
        # Stop the loop when the cog is unloaded
        self.update_user_data.cancel()
    
    # Define the rank command
    @commands.command()
    async def rank(ctx, user: discord.Member = None):
        """Show the user's rank based on their level and experience.

        Args:
            ctx (commands.Context): The context of the command invocation.
            user (discord.Member, optional): The user whose rank to show. Defaults to the author of the message.
        """
        # Create a session to interact with the database
        session = Session()

        # If no user is specified, use the author of the message
        if user is None:
            user = ctx.author

        # Check if the user is in the data
        user_data = session.query(User).get(user.id)
        if user_data is not None:
            # If yes, get their level and experience
            level = user_data.level
            experience = user_data.experience
            # Format the output
            output = f"{user.mention} is at level {level} with {experience} XP."
        else:
            # If not, send a message that they have no rank yet
            output = f"{user.mention} has no rank yet."

        # Send the output
        await ctx.send(output)

        # Close the session
        session.close()

    # Define the pg_pool_check function to check if the pg_pool attribute is created before running the command
    async def pg_pool_check(ctx):
        """Check if the pg_pool attribute is created before running the command."""
        # Return True if the pg_pool attribute exists, False otherwise
        return hasattr(ctx.bot, "pg_pool")

def setup(bot):
    bot.add_cog(Rank(bot))
