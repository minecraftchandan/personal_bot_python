import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import asyncio

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix='m', intents=intents)

@bot.event
async def on_ready():
    print(f'🤖 Logged in as {bot.user}')
    
    # Load all cogs
    cogs = ['cogs.collection','cogs.guess', 'cogs.help', 'cogs.message', 'cogs.pog', 'cogs.dm', 'cogs.msl']
    for cog in cogs:
        try:
            if cog in bot.extensions:
                await bot.reload_extension(cog)
                print(f'🔄 Reloaded {cog}')
            else:
                await bot.load_extension(cog)
                print(f'✅ Loaded {cog}')
        except Exception as e:
            print(f'❌ Failed to load {cog}: {e}')
    
    # Sync slash commands
    try:
        synced = await bot.tree.sync()
        print(f'✅ Synced {len(synced)} slash commands')
    except Exception as e:
        print(f'❌ Failed to sync commands: {e}')

if __name__ == '__main__':
    bot.run(os.getenv('TOKEN'))