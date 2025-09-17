import discord
from discord.ext import commands
import json
import random
import aiohttp
from PIL import Image, ImageFilter
from io import BytesIO
import asyncio
import time

class Guess(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data = self.load_data()
        self.cooldowns = {}
        self.COOLDOWN_TIME = 2
    
    def load_data(self):
        try:
            with open('data/data.json', 'r') as f:
                return json.load(f)
        except:
            return {}
    
    def check_cooldown(self, user_id):
        now = time.time()
        if user_id in self.cooldowns:
            if now < self.cooldowns[user_id]:
                remaining = int(self.cooldowns[user_id] - now)
                return remaining
        
        self.cooldowns[user_id] = now + self.COOLDOWN_TIME
        return 0
    
    @commands.command(name='guess', aliases=['mguess'])
    async def guess_game(self, ctx):
        """Start a character guessing game"""
        # Check cooldown
        remaining = self.check_cooldown(ctx.author.id)
        if remaining > 0:
            await ctx.reply(f'⏳ Please wait **{remaining} second(s)** before guessing again.')
            return
        
        if not self.data:
            await ctx.reply('❌ No character data available.')
            return
        
        # Select random character
        names = list(self.data.keys())
        correct_name = random.choice(names)
        image_url = self.data[correct_name]
        
        try:
            # Download and process image
            async with aiohttp.ClientSession() as session:
                async with session.get(image_url, headers={'User-Agent': 'Mozilla/5.0'}) as response:
                    img_data = await response.read()
            
            image = Image.open(BytesIO(img_data))
            width, height = image.size
            
            # Create crop dimensions
            crop_width = min(200, int(width * 0.3))
            crop_height = min(200, int(height * 0.3))
            
            if crop_width <= 0 or crop_height <= 0:
                raise Exception('Image too small to crop')
            
            # Random crop position
            left = random.randint(0, width - crop_width)
            top = random.randint(0, height - crop_height)
            
            # Crop image
            cropped = image.crop((left, top, left + crop_width, top + crop_height))
            
            # Maybe blur
            should_blur = random.choice([True, False])
            if should_blur:
                cropped = cropped.filter(ImageFilter.GaussianBlur(radius=8))
            
            # Convert to bytes
            buffer = BytesIO()
            cropped.save(buffer, format='PNG')
            buffer.seek(0)
            
            puzzle_file = discord.File(buffer, filename='puzzle.png')
            
            # Create puzzle embed
            embed = discord.Embed(
                title='🧠 Guess the Character',
                description='You have **20 seconds** to guess the character!',
                color=0x5865F2
            )
            embed.set_image(url='attachment://puzzle.png')
            embed.set_footer(text='First correct answer wins!')
            
            puzzle_message = await ctx.send(embed=embed, file=puzzle_file)
            
            print(f'✅ Sent {"blurred" if should_blur else "cropped"} puzzle for {correct_name}')
            
            # Wait for answers
            answered_correctly = False
            
            def check(m):
                return not m.author.bot and m.channel == ctx.channel
            
            try:
                while True:
                    message = await self.bot.wait_for('message', check=check, timeout=20.0)
                    
                    if correct_name.lower() in message.content.lower():
                        answered_correctly = True
                        
                        await puzzle_message.reply(f'🎉 {message.author.mention} guessed it right! It was **{correct_name}**!')
                        
                        # Show full image
                        full_buffer = BytesIO(img_data)
                        full_file = discord.File(full_buffer, filename='full.png')
                        
                        full_embed = discord.Embed(
                            title=f'🎯 It was: {correct_name}',
                            color=0x1ABC9C
                        )
                        full_embed.set_image(url='attachment://full.png')
                        full_embed.set_footer(text='Thanks for playing! 🔍')
                        
                        await puzzle_message.edit(embed=full_embed, attachments=[full_file])
                        break
                        
            except asyncio.TimeoutError:
                if not answered_correctly:
                    await puzzle_message.reply(f'⏰ Time\'s up! The correct answer was **{correct_name}**.')
                    
                    # Show full image
                    full_buffer = BytesIO(img_data)
                    full_file = discord.File(full_buffer, filename='full.png')
                    
                    full_embed = discord.Embed(
                        title=f'🎯 It was: {correct_name}',
                        color=0x1ABC9C
                    )
                    full_embed.set_image(url='attachment://full.png')
                    full_embed.set_footer(text='Thanks for playing! 🔍')
                    
                    await puzzle_message.edit(embed=full_embed, attachments=[full_file])
        
        except Exception as e:
            print(f'❌ Error: {e}')
            await ctx.reply('Error loading character. Please try again!')
            # Remove cooldown on error
            if ctx.author.id in self.cooldowns:
                del self.cooldowns[ctx.author.id]

async def setup(bot):
    await bot.add_cog(Guess(bot))