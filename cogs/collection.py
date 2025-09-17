import discord
from discord.ext import commands
import json
import os

class Collection(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.inventory_dir = 'data/inventory'
        os.makedirs(self.inventory_dir, exist_ok=True)
    
    def get_inventory_path(self, username):
        return os.path.join(self.inventory_dir, f"{username}.json")
    
    def load_inventory(self, username):
        path = self.get_inventory_path(username)
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except:
            return []
    
    @commands.command(name='c')
    async def view_collection(self, ctx):
        """View all card codes in your collection"""
        inventory = self.load_inventory(ctx.author.name)
        
        if not inventory:
            await ctx.reply('📭 You have no cards in your collection.')
            return
        
        codes = '\n'.join([f'🔹 `{card["code"]}`' for card in inventory])
        
        embed = discord.Embed(
            title=f"{ctx.author.name}'s Collection",
            description=codes,
            color=0x3498db
        )
        
        await ctx.reply(embed=embed)
    
    @commands.command(name='v')
    async def view_card(self, ctx, code: str = None):
        """View a specific card by code"""
        if not code:
            await ctx.reply('❌ Please provide a card code. Example: `mv abcd1234`')
            return
        
        inventory = self.load_inventory(ctx.author.name)
        card = next((c for c in inventory if c['code'] == code), None)
        
        if not card:
            await ctx.reply(f'❌ No card found with code `{code}`.')
            return
        
        embed = discord.Embed(
            title=f"Card Code: {code}",
            color=0x00bcd4
        )
        embed.set_image(url=card['imageUrl'])
        embed.set_footer(text=f"{ctx.author.name}'s Card")
        
        await ctx.reply(embed=embed)

async def setup(bot):
    await bot.add_cog(Collection(bot))