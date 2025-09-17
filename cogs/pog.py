import discord
from discord.ext import commands
from discord import app_commands
import re
import aiohttp
import easyocr
import cv2
import numpy as np
import asyncio
from fuzzywuzzy import fuzz
from config.database import mongodb

class POG(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ATTACHMENT_BOT_ID = 853629533855809596
        self.config_cache = {}  # Cache server configs
        use_gpu = False
        try:
            import torch
            use_gpu = torch.cuda.is_available()
        except:
            pass

        self.ocr_reader = easyocr.Reader(['en'], gpu=use_gpu)
        print(f'🚀 POG detection with OCR (GPU={use_gpu})')

    async def get_server_config(self, guild_id):
        """Get server configuration with caching"""
        guild_str = str(guild_id)
        if guild_str in self.config_cache:
            return self.config_cache[guild_str]
        collection = mongodb.get_collection('servers')
        config = await collection.find_one({'guild_id': guild_str})
        result = config if config else {}
        self.config_cache[guild_str] = result
        return result

    async def save_server_config(self, guild_id, target_channel_id):
        """Save server configuration to MongoDB"""
        collection = mongodb.get_collection('servers')
        await collection.update_one(
            {'guild_id': str(guild_id)},
            {'$set': {'guild_id': str(guild_id), 'targetChannelId': target_channel_id}},
            upsert=True
        )
        self.config_cache[str(guild_id)] = {'guild_id': str(guild_id), 'targetChannelId': target_channel_id}

    @app_commands.command(name="setchannel", description="Set the target channel for POG alerts")
    async def set_channel(self, interaction: discord.Interaction, channelid: str):
        guild_id = str(interaction.guild.id)
        try:
            channel = await self.bot.fetch_channel(int(channelid))
            if not hasattr(channel, 'send'):
                await interaction.response.send_message('❌ Invalid channel - cannot send messages.')
                return
        except:
            await interaction.response.send_message('❌ Invalid channel ID.')
            return
        await self.save_server_config(guild_id, int(channelid))
        await interaction.response.send_message(f'✅ Target channel set to <#{channelid}>')

    @commands.Cog.listener()
    async def on_message(self, message):
        if (message.author.id != 742070928111960155 or
            not message.content or
            '<:noriclock:' in message.content):
            return
        guild_id = str(message.guild.id)
        config = await self.get_server_config(guild_id)
        if not config or 'targetChannelId' not in config:
            return
        content = message.content
        if ('0]' in content or
            not any(x in content for x in ['1]', '2]', '3]'])):
            return
        pog_cards = []
        for line in content.split('\n'):
            if not re.match(r'^`?[123]\]', line.strip()):
                continue
            heart_match = re.search(r':heart:\s+`(\d+)', line)
            gid_match = re.search(r'`ɢ\s*(\d+)', line)
            name_match = re.search(r'`[0-9]+\]\s+.+?•\s+\*\*(.+?)\*\*', line)
            hearts = int(heart_match.group(1)) if heart_match else 0
            gid = int(gid_match.group(1)) if gid_match else None
            card_name = name_match.group(1).strip() if name_match else None
            if hearts > 99 or (gid and gid < 100):
                pog_cards.append({'name': card_name, 'gid': gid, 'hearts': hearts})
        if pog_cards:
            print(f'🎯 POG detected! Cards: {pog_cards}')
            await self.handle_pog(message, int(config['targetChannelId']), pog_cards, guild_id)

    async def handle_pog(self, message, target_channel_id, pog_cards, guild_id):
        first_image = None
        mentioned_user = None
        async for msg in message.channel.history(limit=3, before=message):
            if msg.author.id not in [742070928111960155, self.ATTACHMENT_BOT_ID]:
                continue
            if msg.attachments:
                first_image = {'imageUrl': msg.attachments[0].url, 'msg': msg}
                mentioned_user = msg.mentions[0] if msg.mentions else None
                break
            if msg.embeds and msg.embeds[0].image:
                first_image = {'imageUrl': msg.embeds[0].image.url, 'msg': msg}
                mentioned_user = msg.mentions[0] if msg.mentions else None
                break
        if not first_image:
            return
        try:
            await message.channel.send(f'🎉 {mentioned_user.mention if mentioned_user else "<@853629533855809596>"} Pogged! Check it out in <#{target_channel_id}>')
        except:
            pass
        asyncio.create_task(self.verify_and_send_embed(
            target_channel_id, first_image, mentioned_user, message, pog_cards
        ))

    def extract_card_fields_from_image(self, img, card_count=3):
        """
        Extracts name, series, and gen for up to 3 cards using nori repo's coordinates.
        Returns: List of dicts: {'card': idx, 'name': str, 'series': str, 'gen': str}
        """
        # nori repo coordinates for Sofi drop (name, series, gen for 3 cards)
        coords = [
            # Card 1
            (12, 458, 290, 26),    # name
            (12, 487, 290, 26),    # series
            (36, 427, 108, 26),    # gen
            # Card 2
            (361, 458, 290, 26),   # name
            (361, 487, 290, 26),   # series
            (385, 427, 108, 26),   # gen
            # Card 3
            (704, 458, 290, 26),   # name
            (704, 487, 290, 26),   # series
            (728, 427, 108, 26),   # gen
        ]
        results = []
        for idx in range(card_count):
            name_roi = img[coords[idx*3+0][1]:coords[idx*3+0][1]+coords[idx*3+0][3], coords[idx*3+0][0]:coords[idx*3+0][0]+coords[idx*3+0][2]]
            name_text = ' '.join([t[1] for t in self.ocr_reader.readtext(name_roi)]).strip()
            series_roi = img[coords[idx*3+1][1]:coords[idx*3+1][1]+coords[idx*3+1][3], coords[idx*3+1][0]:coords[idx*3+1][0]+coords[idx*3+1][2]]
            series_text = ' '.join([t[1] for t in self.ocr_reader.readtext(series_roi)]).strip()
            gen_roi = img[coords[idx*3+2][1]:coords[idx*3+2][1]+coords[idx*3+2][3], coords[idx*3+2][0]:coords[idx*3+2][0]+coords[idx*3+2][2]]
            gen_text = ' '.join([t[1] for t in self.ocr_reader.readtext(gen_roi)]).strip()
            results.append({'card': idx+1, 'name': name_text, 'series': series_text, 'gen': gen_text})
        return results

    async def verify_and_send_embed(self, target_channel_id, first_image, mentioned_user, message, pog_cards):
        """
        OCR verification: succeeds if any card matches, sends embed, skips further checks
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(first_image['imageUrl']) as response:
                    image_data = await response.read()
            nparr = np.frombuffer(image_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if img is None:
                return

            # Extract name, series, gen using nori coordinates
            card_fields = self.extract_card_fields_from_image(img, card_count=3)
            print("Extracted card fields:", card_fields)

            verified = False
            verified_card = None
            for card in pog_cards:
                for field in card_fields:
                    # Name fuzzy match or gen exact match
                    if card['name'] and fuzz.partial_ratio(card['name'].lower(), field['name'].lower()) > 70:
                        print(f'✅ OCR name matched: {card["name"]} ~ {field["name"]}')
                        verified = True
                        verified_card = card
                        break
                    if card['gid'] and str(card['gid']) == field['gen']:
                        print(f'✅ OCR gen matched: {card["gid"]} ~ {field["gen"]}')
                        verified = True
                        verified_card = card
                        break
                if verified:
                    break  # Exit outer loop as soon as one card is verified

            if verified:
                embed = discord.Embed(
                    title='<a:AnimeGirljumping:1365978464435441675> 𝑷𝑶𝑮𝑮𝑬𝑹𝑺 <a:brown_jump:1365979505977458708>',
                    description=f'{mentioned_user.mention if mentioned_user else "Unknown"} triggered a POG!\n\n{message.content}\n\n**Attachment:**',
                    color=0x87CEEB
                )
                embed.set_image(url=first_image['imageUrl'])
                embed.set_footer(text=f'Dropped by: {mentioned_user.display_name if mentioned_user else "Unknown"}')
                view = discord.ui.View()
                view.add_item(discord.ui.Button(
                    label='Jump to Message',
                    style=discord.ButtonStyle.link,
                    url=first_image['msg'].jump_url
                ))
                target_channel = self.bot.get_channel(target_channel_id) or await self.bot.fetch_channel(target_channel_id)
                if target_channel:
                    await target_channel.send(embed=embed, view=view)
            else:
                print(f'❌ OCR verification failed for all cards - cant send embed')
        except Exception as e:
            print(f'OCR verification error: {e}')

    def clear_cache(self):
        """Clear config cache"""
        self.config_cache.clear()

async def setup(bot):
    await mongodb.connect()
    pog_cog = POG(bot)
    await bot.add_cog(pog_cog)
    import asyncio
    async def cache_cleaner():
        while True:
            await asyncio.sleep(300)
            pog_cog.clear_cache()
    asyncio.create_task(cache_cleaner())