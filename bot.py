import os
import re
import discord
import asyncio
import yt_dlp
from io import BytesIO
from dotenv import load_dotenv
from discord.ext import commands
from discord import app_commands
from discord.ui import View, ChannelSelect, Button
from spotipy.oauth2 import SpotifyClientCredentials
import spotipy

# Load tokens from .env
load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
SPOTIPY_CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
SPOTIPY_CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")

# Setup
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=SPOTIPY_CLIENT_ID,
    client_secret=SPOTIPY_CLIENT_SECRET
))

# Configs
WELCOME_CONFIG = {"channel_id": None, "message_template": None}
TICKET_CONFIG = {"ticket_category_id": None, "log_channel_id": None, "authorized_roles": set()}

# -------------------- Bot Ready --------------------
@bot.event
async def on_ready():
    for guild in bot.guilds:
        await tree.sync(guild=discord.Object(id=guild.id))
        print(f"✅ Slash commands synced in: {guild.name} ({guild.id})")
    print(f"🤖 Logged in as {bot.user}")

# -------------------- Welcome System --------------------
@tree.command(name="setwelcome", description="Set welcome channel and message.")
@app_commands.describe(channel="Where to send welcome", message="Message: {member}, {servername}, {count}")
async def setwelcome(interaction: discord.Interaction, channel: discord.TextChannel, message: str):
    WELCOME_CONFIG["channel_id"] = channel.id
    WELCOME_CONFIG["message_template"] = message
    await interaction.response.send_message(f"✅ Welcome message set for {channel.mention}", ephemeral=True)

@bot.event
async def on_member_join(member):
    cid = WELCOME_CONFIG.get("channel_id")
    msg_template = WELCOME_CONFIG.get("message_template")
    if not cid or not msg_template:
        return

    channel = member.guild.get_channel(cid)
    if channel:
        msg = msg_template.replace("{member}", member.mention)
        msg = msg.replace("{count}", str(len(member.guild.members)))
        msg = msg.replace("{servername}", member.guild.name)

        embed = discord.Embed(description=msg, color=discord.Color.green())
        if member.guild.icon:
            embed.set_thumbnail(url=member.guild.icon.url)
        await channel.send(embed=embed)

# -------------------- Ticket Setup --------------------
@tree.command(name="setup", description="Show ticket setup help")
@app_commands.checks.has_permissions(administrator=True)
async def setup(interaction: discord.Interaction):
    embed = discord.Embed(title="🛠 Ticket Bot Setup", color=discord.Color.orange())
    embed.add_field(name="/setcategory", value="Select category to hold ticket channels", inline=False)
    embed.add_field(name="/setlogs", value="Select channel for logs", inline=False)
    embed.add_field(name="/sendpanel", value="Send ticket creation button", inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)

@tree.command(name="setcategory", description="Set category for ticket channels")
@app_commands.checks.has_permissions(administrator=True)
async def setcategory(interaction: discord.Interaction):
    class CategorySelect(ChannelSelect):
        def __init__(self):
            super().__init__(channel_types=[discord.ChannelType.category])

        async def callback(self, i: discord.Interaction):
            TICKET_CONFIG["ticket_category_id"] = self.values[0].id
            await i.response.send_message(f"✅ Ticket category set to `{self.values[0].name}`", ephemeral=True)

    await interaction.response.send_message("📂 Choose ticket category:", view=View().add_item(CategorySelect()), ephemeral=True)

@tree.command(name="setlogs", description="Set log channel")
@app_commands.checks.has_permissions(administrator=True)
async def setlogs(interaction: discord.Interaction):
    class LogSelect(ChannelSelect):
        def __init__(self):
            super().__init__(channel_types=[discord.ChannelType.text])

        async def callback(self, i: discord.Interaction):
            TICKET_CONFIG["log_channel_id"] = self.values[0].id
            await i.response.send_message(f"📝 Log channel set to {self.values[0].mention}", ephemeral=True)

    await interaction.response.send_message("🪵 Choose log channel:", view=View().add_item(LogSelect()), ephemeral=True)

# -------------------- Ticket Panel --------------------
class TicketView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🎟 Create Ticket", style=discord.ButtonStyle.green, custom_id="ticket_create")
    async def create_ticket(self, interaction: discord.Interaction, button: Button):
        user = interaction.user
        guild = interaction.guild
        category = guild.get_channel(TICKET_CONFIG["ticket_category_id"])
        if not category:
            return await interaction.response.send_message("❌ Ticket category not set.", ephemeral=True)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }

        for role_id in TICKET_CONFIG["authorized_roles"]:
            role = guild.get_role(role_id)
            if role:
                overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

        channel = await guild.create_text_channel(
            name=f"ticket-{user.name}",
            category=category,
            overwrites=overwrites
        )

        await channel.send(f"{user.mention} 🎫 Your support ticket has been created.")
        await interaction.response.send_message(f"✅ Ticket created: {channel.mention}", ephemeral=True)

        log = guild.get_channel(TICKET_CONFIG.get("log_channel_id"))
        if log:
            await log.send(f"📨 New ticket by {user.mention}: {channel.mention}")

@tree.command(name="sendpanel", description="Send the ticket panel")
@app_commands.checks.has_permissions(administrator=True)
async def sendpanel(interaction: discord.Interaction):
    embed = discord.Embed(title="📩 Need Help?", description="Click the button below to open a support ticket.", color=discord.Color.blurple())
    await interaction.channel.send(embed=embed, view=TicketView())
    await interaction.response.send_message("✅ Ticket panel sent!", ephemeral=True)

@tree.command(name="close", description="Close this ticket channel")
async def close(interaction: discord.Interaction):
    if TICKET_CONFIG["ticket_category_id"] != interaction.channel.category_id:
        return await interaction.response.send_message("❌ Not a ticket channel.", ephemeral=True)

    allowed = (
        interaction.channel.name.endswith(interaction.user.name.lower())
        or any(role.id in TICKET_CONFIG["authorized_roles"] for role in interaction.user.roles)
        or interaction.user.guild_permissions.administrator
    )

    if not allowed:
        return await interaction.response.send_message("🚫 You can't close this ticket.", ephemeral=True)

    await interaction.response.send_message("🛑 Closing ticket in 5 seconds...")
    await asyncio.sleep(5)
    await interaction.channel.delete()

    log = interaction.guild.get_channel(TICKET_CONFIG.get("log_channel_id"))
    if log:
        await log.send(f"🔒 Ticket closed by {interaction.user.mention}: `{interaction.channel.name}`")

# -------------------- Run --------------------
bot.run(TOKEN)
