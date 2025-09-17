import discord
from discord.ext import commands
import asyncio

class MSL(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.owner_id = 587709425708695552
    
    @commands.command(name='sl', aliases=['msl'])
    async def server_list(self, ctx):
        """List all servers the bot is in (owner only)"""
        if ctx.author.id != self.owner_id:
            return
        
        guilds = list(self.bot.guilds)
        per_page = 5
        page = 0
        total_pages = (len(guilds) + per_page - 1) // per_page
        
        view = ServerListView(guilds, page, per_page, total_pages, ctx.author)
        embed = await view.generate_embed()
        
        await ctx.reply(embed=embed, view=view)

class ServerListView(discord.ui.View):
    def __init__(self, guilds, page, per_page, total_pages, author):
        super().__init__(timeout=30)
        self.guilds = guilds
        self.page = page
        self.per_page = per_page
        self.total_pages = total_pages
        self.author = author
    
    async def generate_embed(self):
        start = self.page * self.per_page
        end = start + self.per_page
        page_guilds = self.guilds[start:end]
        
        embed = discord.Embed(
            title='🧭 Servers the Bot is In',
            color=discord.Color.random()
        )
        embed.set_footer(text=f'Page {self.page + 1} of {self.total_pages}')
        
        for i, guild in enumerate(page_guilds):
            invite = '❌ No invite could be created'
            
            try:
                # Find a channel where bot can create invites
                for channel in guild.text_channels:
                    if channel.permissions_for(guild.me).create_instant_invite:
                        try:
                            invite_obj = await channel.create_invite(
                                max_age=0,
                                max_uses=0,
                                reason='Auto-generated for bot owner'
                            )
                            invite = f'[link]({invite_obj.url})'
                            break
                        except:
                            continue
            except:
                invite = '❌ Failed to fetch invite'
            
            embed.add_field(
                name=f'{start + i + 1}. {guild.name}',
                value=f'🆔 {guild.id}\n🔗 {invite}',
                inline=False
            )
        
        return embed
    
    @discord.ui.button(label='⬅ Previous', style=discord.ButtonStyle.primary)
    async def previous_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.author:
            await interaction.response.send_message('❌ SOJA BRO', ephemeral=True)
            return
        
        self.page = (self.page - 1) % self.total_pages
        embed = await self.generate_embed()
        await interaction.response.edit_message(embed=embed, view=self)
    
    @discord.ui.button(label='Next ➡', style=discord.ButtonStyle.primary)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.author:
            await interaction.response.send_message('❌ SOJA BRO', ephemeral=True)
            return
        
        self.page = (self.page + 1) % self.total_pages
        embed = await self.generate_embed()
        await interaction.response.edit_message(embed=embed, view=self)
    
    async def on_timeout(self):
        for item in self.children:
            item.disabled = True

async def setup(bot):
    await bot.add_cog(MSL(bot))