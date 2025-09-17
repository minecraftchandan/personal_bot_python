import discord
from discord.ext import commands
import firebase_admin
from firebase_admin import credentials, firestore
import os
from datetime import datetime

class Message(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = self.init_firebase()
        self.allowed_user_id = 587709425708695552
    
    def init_firebase(self):
        try:
            if not firebase_admin._apps:
                cred = credentials.Certificate('data/serviceAccountKey.json')
                firebase_admin.initialize_app(cred)
            return firestore.client()
        except Exception as e:
            print(f"Firebase initialization error: {e}")
            return None
    
    def format_ist(self, timestamp):
        try:
            if hasattr(timestamp, 'to_pydatetime'):
                date = timestamp.to_pydatetime()
            else:
                date = datetime.fromisoformat(str(timestamp))
            
            return date.strftime('%d %B %Y | %I:%M %p IST')
        except Exception as e:
            print(f'Timestamp parse error: {e}')
            return 'Invalid Timestamp'
    
    @commands.command(name='s')
    async def view_messages(self, ctx):
        """View contact messages (owner only)"""
        if ctx.author.id != self.allowed_user_id:
            await ctx.reply('🚫 WHALES NOT ALLOWED.')
            return
        
        if not self.db:
            await ctx.reply('❌ Database not available.')
            return
        
        # Get messages from Firestore
        try:
            docs = self.db.collection('contact').order_by('timestamp', direction=firestore.Query.DESCENDING).get()
            all_messages = [doc.to_dict() for doc in docs]
        except Exception as e:
            await ctx.reply(f'❌ Error fetching messages: {e}')
            return
        
        if not all_messages:
            await ctx.reply('📭 No messages found.')
            return
        
        # Pagination setup
        page = 0
        per_page = 5
        total_pages = (len(all_messages) + per_page - 1) // per_page
        
        view = MessagePaginationView(all_messages, page, per_page, total_pages, self, ctx.author)
        embed = view.generate_embed()
        
        await ctx.reply(embed=embed, view=view)

class MessagePaginationView(discord.ui.View):
    def __init__(self, messages, page, per_page, total_pages, cog, author):
        super().__init__(timeout=300)
        self.messages = messages
        self.page = page
        self.per_page = per_page
        self.total_pages = total_pages
        self.cog = cog
        self.author = author
        self.viewing_message = False
    
    def generate_embed(self):
        if self.viewing_message:
            return self.current_message_embed
        
        start = self.page * self.per_page
        page_messages = self.messages[start:start + self.per_page]
        
        embed = discord.Embed(
            title='📩 Contact Messages',
            color=0x5865F2
        )
        embed.set_footer(text=f'Page {self.page + 1} of {self.total_pages}')
        
        for msg in page_messages:
            embed.add_field(
                name=msg.get('username', 'Unknown'),
                value=self.cog.format_ist(msg.get('timestamp')),
                inline=False
            )
        
        return embed
    
    def generate_select_menu(self):
        start = self.page * self.per_page
        page_messages = self.messages[start:start + self.per_page]
        
        options = []
        for i, msg in enumerate(page_messages):
            options.append(discord.SelectOption(
                label=msg.get('username', 'Unknown'),
                description=self.cog.format_ist(msg.get('timestamp')),
                value=str(start + i)
            ))
        
        select = discord.ui.Select(
            placeholder='Select a user to view full message',
            options=options
        )
        select.callback = self.select_callback
        return select
    
    async def select_callback(self, interaction):
        if interaction.user != self.author:
            await interaction.response.send_message('Not for you.', ephemeral=True)
            return
        
        index = int(interaction.values[0])
        data = self.messages[index]
        
        self.current_message_embed = discord.Embed(
            title=f'📨 Message from {data.get("username", "Unknown")}',
            description=data.get('message', 'No message content'),
            color=0x00FF00
        )
        self.current_message_embed.set_footer(text=self.cog.format_ist(data.get('timestamp')))
        
        self.viewing_message = True
        self.clear_items()
        self.add_item(self.back_button())
        
        await interaction.response.edit_message(embed=self.current_message_embed, view=self)
    
    def back_button(self):
        button = discord.ui.Button(label='🔙 Back', style=discord.ButtonStyle.primary)
        button.callback = self.back_callback
        return button
    
    async def back_callback(self, interaction):
        if interaction.user != self.author:
            await interaction.response.send_message('Not for you.', ephemeral=True)
            return
        
        self.viewing_message = False
        self.clear_items()
        self.add_navigation_buttons()
        self.add_item(self.generate_select_menu())
        
        await interaction.response.edit_message(embed=self.generate_embed(), view=self)
    
    def add_navigation_buttons(self):
        # First, Previous, Next, Last buttons
        first_btn = discord.ui.Button(label='⏮️', style=discord.ButtonStyle.secondary)
        prev_btn = discord.ui.Button(label='⬅️', style=discord.ButtonStyle.secondary)
        next_btn = discord.ui.Button(label='➡️', style=discord.ButtonStyle.secondary)
        last_btn = discord.ui.Button(label='⏭️', style=discord.ButtonStyle.secondary)
        
        first_btn.callback = lambda i: self.navigate_callback(i, 0)
        prev_btn.callback = lambda i: self.navigate_callback(i, max(0, self.page - 1))
        next_btn.callback = lambda i: self.navigate_callback(i, min(self.total_pages - 1, self.page + 1))
        last_btn.callback = lambda i: self.navigate_callback(i, self.total_pages - 1)
        
        self.add_item(first_btn)
        self.add_item(prev_btn)
        self.add_item(next_btn)
        self.add_item(last_btn)
    
    async def navigate_callback(self, interaction, new_page):
        if interaction.user != self.author:
            await interaction.response.send_message('Not for you.', ephemeral=True)
            return
        
        self.page = new_page
        self.clear_items()
        self.add_navigation_buttons()
        self.add_item(self.generate_select_menu())
        
        await interaction.response.edit_message(embed=self.generate_embed(), view=self)

async def setup(bot):
    await bot.add_cog(Message(bot))