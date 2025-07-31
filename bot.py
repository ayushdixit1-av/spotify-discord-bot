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

# Load environment variables
load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
SPOTIPY_CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
SPOTIPY_CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=SPOTIPY_CLIENT_ID,
    client_secret=SPOTIPY_CLIENT_SECRET
))

WELCOME_CONFIG = {"channel_id": None, "message_template": None}
TICKET_CONFIG = {"ticket_category_id": None, "log_channel_id": None, "authorized_roles": set()}

# ----- READY -----
@bot.event
async def on_ready():
    for guild in bot.guilds:
        await tree.sync(guild=discord.Object(id=guild.id))
        print(f"✅ Synced commands in: {guild.name} ({guild.id})")
    print(f"🤖 Logged in as {bot.user}")

# ----- WELCOME -----
@tree.command(name="setwelcome", description="Set welcome channel & message")
@app_commands.describe(channel="Welcome channel", message="Message (use {member}, {servername}, {count})")
async def setwelcome(interaction: discord.Interaction, channel: discord.TextChannel, message: str):
    WELCOME_CONFIG["channel_id"] = channel.id
    WELCOME_CONFIG["message_template"] = message
    await interaction.response.send_message(f"✅ Welcome set to {channel.mention}", ephemeral=True)

@bot.event
async def on_member_join(member):
    channel_id = WELCOME_CONFIG.get("channel_id")
    msg_template = WELCOME_CONFIG.get("message_template")
    if not channel_id or not msg_template:
        return

    channel = member.guild.get_channel(channel_id)
    if channel:
        msg = msg_template.replace("{member}", member.mention)\
                          .replace("{servername}", member.guild.name)\
                          .replace("{count}", str(len(member.guild.members)))
        embed = discord.Embed(description=msg, color=discord.Color.green())
        if member.guild.icon:
            embed.set_thumbnail(url=member.guild.icon.url)
        await channel.send(embed=embed)

# ----- TICKETS -----
@tree.command(name="setup", description="Show ticket setup options")
@app_commands.checks.has_permissions(administrator=True)
async def setup(interaction: discord.Interaction):
    embed = discord.Embed(title="🎫 Ticket Setup", color=discord.Color.orange())
    embed.add_field(name="/setcategory", value="Set ticket category", inline=False)
    embed.add_field(name="/setlogs", value="Set log channel", inline=False)
    embed.add_field(name="/sendpanel", value="Send ticket button", inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)

@tree.command(name="setcategory", description="Set category for tickets")
@app_commands.checks.has_permissions(administrator=True)
async def setcategory(interaction: discord.Interaction):
    class CategorySelect(ChannelSelect):
        def __init__(self):
            super().__init__(channel_types=[discord.ChannelType.category])

        async def callback(self, i: discord.Interaction):
            TICKET_CONFIG["ticket_category_id"] = self.values[0].id
            await i.response.send_message(f"📁 Ticket category set: {self.values[0].name}", ephemeral=True)

    await interaction.response.send_message("📂 Choose category:", view=View().add_item(CategorySelect()), ephemeral=True)

@tree.command(name="setlogs", description="Set ticket log channel")
@app_commands.checks.has_permissions(administrator=True)
async def setlogs(interaction: discord.Interaction):
    class LogSelect(ChannelSelect):
        def __init__(self):
            super().__init__(channel_types=[discord.ChannelType.text])

        async def callback(self, i: discord.Interaction):
            TICKET_CONFIG["log_channel_id"] = self.values[0].id
            await i.response.send_message(f"📝 Log channel set to {self.values[0].mention}", ephemeral=True)

    await interaction.response.send_message("🪵 Choose log channel:", view=View().add_item(LogSelect()), ephemeral=True)

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

        await channel.send(f"{user.mention} 🎫 Your ticket has been created.")
        await interaction.response.send_message(f"✅ Ticket: {channel.mention}", ephemeral=True)

        log = guild.get_channel(TICKET_CONFIG["log_channel_id"])
        if log:
            await log.send(f"📨 Ticket by {user.mention}: {channel.mention}")

@tree.command(name="sendpanel", description="Send ticket creation panel")
@app_commands.checks.has_permissions(administrator=True)
async def sendpanel(interaction: discord.Interaction):
    embed = discord.Embed(title="📩 Need Help?", description="Click the button to open a ticket.", color=discord.Color.blurple())
    await interaction.channel.send(embed=embed, view=TicketView())
    await interaction.response.send_message("✅ Panel sent.", ephemeral=True)

@tree.command(name="close", description="Close this ticket")
async def close(interaction: discord.Interaction):
    if TICKET_CONFIG["ticket_category_id"] != interaction.channel.category_id:
        return await interaction.response.send_message("❌ Not a ticket channel.", ephemeral=True)

    user = interaction.user
    allowed = (
        interaction.channel.name.endswith(user.name.lower()) or
        any(role.id in TICKET_CONFIG["authorized_roles"] for role in user.roles) or
        user.guild_permissions.administrator
    )

    if not allowed:
        return await interaction.response.send_message("🚫 You can't close this ticket.", ephemeral=True)

    await interaction.response.send_message("🛑 Closing in 5 seconds...")
    await asyncio.sleep(5)
    await interaction.channel.delete()

    log = interaction.guild.get_channel(TICKET_CONFIG.get("log_channel_id"))
    if log:
        await log.send(f"🔒 Ticket closed by {user.mention}: `{interaction.channel.name}`")

# ----- RUN -----
if not TOKEN:
    print("❌ DISCORD_BOT_TOKEN not found.")
else:
    bot.run(TOKEN)
