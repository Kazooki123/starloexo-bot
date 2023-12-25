import asyncio
from discord.ext import commands

# Define the cooldown parameters (you can adjust these values)
COOLDOWN_RATE = 15  # Number of messages needed for a level-up
COOLDOWN_SECONDS = 60  # Cooldown time in seconds

async def get_user_data(user_id):
    # Replace this with your actual implementation to get or initialize user data
    # For example, interacting with a database or cache
    user_data = {'messages_count': 0, 'level': 0, 'rank': 0}  # Replace with actual data retrieval logic
    return user_data

# Use the commands.cooldown decorator to apply the cooldown
@commands.cooldown(1, COOLDOWN_SECONDS, commands.BucketType.user)
async def process_leveling(message, user_data):
    user_id = message.author.id

    if user_id not in user_data:
        user_data[user_id] = {'messages_count': 0, 'level': 0, 'rank': 0}

    # Increment the messages count for the user
    user_data[user_id]['messages_count'] += 1

    # Check if the user has sent enough messages to level up
    if user_data[user_id]['messages_count'] >= COOLDOWN_RATE:
        user_data[user_id]['messages_count'] = 0
        user_data[user_id]['level'] += 1

        # Cap the level at 50
        if user_data[user_id]['level'] > 50:
            user_data[user_id]['level'] = 50

        # Inform the user about their new level and rank
        await message.channel.send(f"{message.author.mention}, you leveled up to Level {user_data[user_id]['level']}!")

@commands.cooldown(1, COOLDOWN_SECONDS, commands.BucketType.user)
async def process_ranks(message, user_data):
    user_id = message.author.id

    # Calculate the rank based on the level
    user_data[user_id]['rank'] = user_data[user_id]['level'] // 15

    # Cap the rank at 50
    if user_data[user_id]['rank'] > 50:
        user_data[user_id]['rank'] = 50

    # Inform the user about their rank
    await message.channel.send(f"{message.author.mention}, you are now Rank {user_data[user_id]['rank']}!")

async def get_user_rank(user_id, user_data):
    # Calculate the user's rank based on the level
    rank = user_data.get(user_id, {}).get('level', 0) // 15

    # Cap the rank at 50
    return min(rank, 50)

async def command_rank(ctx, user_data):
    user_id = ctx.message.author.id if not ctx.message.mentions else ctx.message.mentions[0].id

    # Get the user's rank
    rank = await get_user_rank(user_id, user_data)

    # Send the rank information to the channel
    await ctx.send(f"{ctx.message.author.mention if not ctx.message.mentions else ctx.message.mentions[0].mention} is currently level {user_data.get(user_id, {}).get('level', 0)} and rank {rank}!")

# Example usage: !rank @user
