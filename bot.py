import os
import discord
from discord.ext import commands
from discord import app_commands
from spotipy.oauth2 import SpotifyClientCredentials
import spotipy
import asyncio
import yt_dlp
import re
from io import BytesIO

# Environment Variables
DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
SPOTIPY_CLIENT_ID = os.getenv('SPOTIPY_CLIENT_ID')
SPOTIPY_CLIENT_SECRET = os.getenv('SPOTIPY_CLIENT_SECRET')

# Intents
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
intents.members = True

bot = commands.Bot(command_prefix=commands.when_mentioned_or("!"), intents=intents)

sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=SPOTIPY_CLIENT_ID,
    client_secret=SPOTIPY_CLIENT_SECRET
))

# Regex
YOUTUBE_URL_REGEX = r"(?:https?://)?(?:www\.)?(?:youtube\.com|youtu\.be)/(?:watch\?v=|embed/|v/|)([\w-]{11})(?:\S+)?"
SPOTIFY_TRACK_URL_REGEX = r"https?://open\.spotify\.com/track/([a-zA-Z0-9]+)(?:\?.*)?"

# Welcome Config
WELCOME_CONFIG = {
    "channel_id": None,
    "message_template": None
}

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name} ({bot.user.id})")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Error syncing commands: {e}")

@bot.tree.command(name="setwelcome", description="Set the welcome channel and message template.")
@app_commands.describe(channel="The channel to send welcome messages in.", message="The welcome message (use {member}, {count}, {servername}).")
async def set_welcome(interaction: discord.Interaction, channel: discord.TextChannel, message: str):
    WELCOME_CONFIG["channel_id"] = channel.id
    WELCOME_CONFIG["message_template"] = message
    await interaction.response.send_message(f"Welcome channel set to {channel.mention} and message saved.", ephemeral=True)

@bot.event
async def on_member_join(member):
    channel_id = WELCOME_CONFIG.get("channel_id")
    message_template = WELCOME_CONFIG.get("message_template")

    if channel_id and message_template:
        channel = member.guild.get_channel(channel_id)
        if channel:
            count = len(member.guild.members)
            msg = message_template.replace("{member}", member.mention)
            msg = msg.replace("{count}", str(count))
            msg = msg.replace("{servername}", member.guild.name)

            # Get server icon image
            if member.guild.icon:
                icon = member.guild.icon.url
                embed = discord.Embed(description=msg, color=discord.Color.green())
                embed.set_thumbnail(url=icon)
                await channel.send(embed=embed)
            else:
                await channel.send(msg)

# ... Your existing commands for /play, /suggest, etc ...

if __name__ == '__main__':
    if not DISCORD_BOT_TOKEN:
        print("Error: DISCORD_BOT_TOKEN environment variable not set.")
    else:
        bot.run(DISCORD_BOT_TOKEN)
