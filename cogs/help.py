import discord
from discord.ext import commands
import random

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    def get_help_embed(self):
        return discord.Embed(
            title='📜 Available Commands',
            color=random.randint(0, 0xFFFFFF),
            description='Here are all the available commands you can use:'
        ).add_field(
            name='`mdrop`', 
            value='🎴 Drop a card to claim!(prototype)', 
            inline=False
        ).add_field(
            name='`mguess`', 
            value='🧠 Start a "Guess the Genshin Character" game.', 
            inline=False
        ).add_field(
            name='`/message`', 
            value='📩 Send a private message to the bot owner.', 
            inline=False
        ).set_thumbnail(
            url='https://media2.giphy.com/media/v1.Y2lkPTc5MGI3NjExMm5sNmVoMHRzMHU0ejFpNDUxeHJ2bGZvaWhpaW9ka3NxNHEzdTdiayZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/lrDAgsYq0eomhwoESZ/giphy.gif'
        ).set_footer(text='Have fun! :)')
    
    @commands.command(name='mhelp')
    async def help_command(self, ctx):
        """Show all available commands"""
        embed = self.get_help_embed()
        await ctx.reply(embed=embed)
    


async def setup(bot):
    await bot.add_cog(Help(bot))