# In ranks.py
# This module contains the function and command to update and show the user's rank based on their level and experience.

import discord
from discord.ext import commands
import random
import asyncpg.sql as sql # Import the asyncpg.sql module

# Define the table name
TABLE_NAME = "user_data"

# Define the formula to calculate the level from the experience
def level_formula(experience):
    return int(experience ** 0.25)

# Define a function to update the user data
async def update_user_data(user, message, bot): # Remove the db parameter
    """Update the user's level and experience based on their messages.

    Args:
        user (discord.Member): The user who sent the message.
        message (discord.Message): The message that the user sent.
        bot (commands.Bot): The bot object.
    """
    db = bot.pg_pool # Get the pool of connections from the bot object
    # Check if the user is already in the data
    query = sql.SQL("SELECT * FROM {table} WHERE user_id = $1;").format(
        table=sql.Identifier(TABLE_NAME)
    ) # Use the sql.SQL and sql.Identifier classes for parameterized queries
    row = await db.fetchrow(query, user.id)
    if row is None:
        # If not, create a new entry with default values
        query = sql.SQL("INSERT INTO {table} (user_id, level, experience) VALUES ($1, $2, $3);").format(
            table=sql.Identifier(TABLE_NAME)
        ) # Use the sql.SQL and sql.Identifier classes for parameterized queries
        await db.execute(query, user.id, 0, 0)
    # Increment the user's experience by a random amount between 5 and 10
    query = sql.SQL("UPDATE {table} SET experience = experience + $1 WHERE user_id = $2;").format(
        table=sql.Identifier(TABLE_NAME)
    ) # Use the sql.SQL and sql.Identifier classes for parameterized queries
    await db.execute(query, random.randint(5, 10), user.id)
    # Calculate the user's level based on their experience
    # You can use any formula you want, but here's a simple one
    query = sql.SQL("SELECT experience FROM {table} WHERE user_id = $1;").format(
        table=sql.Identifier(TABLE_NAME)
    ) # Use the sql.SQL and sql.Identifier classes for parameterized queries
    row = await db.fetchrow(query, user.id)
    experience = row["experience"]
    # Check if the experience is None before performing the exponentiation operation
    if experience is None:
        # Assign a default value of 0
        experience = 0
    level = level_formula(experience) # Use the level_formula function instead of the hard-coded formula
    # Check if the user has leveled up
    query = sql.SQL("SELECT level FROM {table} WHERE user_id = $1;").format(
        table=sql.Identifier(TABLE_NAME)
    ) # Use the sql.SQL and sql.Identifier classes for parameterized queries
    row = await db.fetchrow(query, user.id)
    old_level = row["level"]
    if old_level is None:
        # Assign a default value of 0
        old_level = 0
    if level > old_level:
        # If yes, update their level and send a message
        query = sql.SQL("UPDATE {table} SET level = $1 WHERE user_id = $2;").format(
            table=sql.Identifier(TABLE_NAME)
        ) # Use the sql.SQL and sql.Identifier classes for parameterized queries
        await db.execute(query, level, user.id)
        await message.channel.send(f"Congrats {user.mention}! You reached level {level} 🥳")

# Define the rank command
@commands.command()
@commands.cog_check(pg_pool_check)
async def rank(ctx, user: discord.Member = None):
    """Show the user's rank based on their level and experience.

    Args:
        ctx (commands.Context): The context of the command invocation.
        user (discord.Member, optional): The user whose rank to show. Defaults to the author of the message.
    """
    db = ctx.bot.pg_pool # Get the pool of connections from the context object
    # If no user is specified, use the author of the message
    if user is None:
        user = ctx.author
    # Check if the user is in the data
    query = sql.SQL("SELECT * FROM {table} WHERE user_id = $1;").format(
        table=sql.Identifier(TABLE_NAME)
    ) # Use the sql.SQL and sql.Identifier classes for parameterized queries
    row = await db.fetchrow(query, user.id)
    if row is not None:
        # If yes, get their level and experience
        level = row["level"]
        experience = row["experience"]
        # Format the output
        output = f"{user.mention} is at level {level} with {experience} XP."
    else:
        # If not, send a message that they have no rank yet
        output = f"{user.mention} has no rank yet."
    # Send the output
    await ctx.send(output)

# Define the pg_pool_check function to check if the pg_pool attribute is created before running the command
async def pg_pool_check(ctx):
    """Check if the pg_pool attribute is created before running the command."""
    # Return True if the pg_pool attribute exists, False otherwise
    return hasattr(ctx.bot, "pg_pool")

# Define the setup function to add the command to the bot
def setup(bot):
    bot.add_command(rank)
