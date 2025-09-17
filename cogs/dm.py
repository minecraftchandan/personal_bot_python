import discord
from discord.ext import commands
from discord import app_commands
import random

class DM(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot_owner_id = 587709425708695552
    
    @app_commands.command(name='message', description='Send a private message to the bot owner')
    async def send_message(self, interaction: discord.Interaction, text: str = None, image: discord.Attachment = None):
        """Send a private message to the bot owner"""
        if not text and not image:
            await interaction.response.send_message('❌ Please provide either text or an image.', ephemeral=True)
            return
            
        try:
            await interaction.response.defer(ephemeral=True)
            
            owner_user = await self.bot.fetch_user(self.bot_owner_id)
            
            embed = discord.Embed(
                title='📩 New Message Received',
                description=f'**{interaction.user}** sent:',
                color=random.randint(0, 0xffffff)
            )
            
            if text:
                embed.add_field(name='Message', value=f'> {text}', inline=False)
            
            if image:
                embed.set_image(url=image.url)
                embed.add_field(name='Image', value=f'[{image.filename}]({image.url})', inline=False)
            
            embed.set_footer(text=f'User ID: {interaction.user.id}')
            embed.timestamp = discord.utils.utcnow()
            
            await owner_user.send(embed=embed)
            
            await interaction.followup.send('✅ Your message was sent to the bot owner!')
            
        except Exception as e:
            print(f'❌ Failed to forward message: {e}')
            await interaction.followup.send('❌ Failed to send your message. Try again later.')

async def setup(bot):
    await bot.add_cog(DM(bot))