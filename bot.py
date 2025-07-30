import os
import discord
from discord.ext import commands
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import asyncio
import yt_dlp # For fetching audio from YouTube

# --- Configuration ---
# Get environment variables for sensitive information
DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
SPOTIPY_CLIENT_ID = os.getenv('SPOTIPY_CLIENT_ID')
SPOTIPY_CLIENT_SECRET = os.getenv('SPOTIPY_CLIENT_SECRET')

# Intents are required for your bot to receive certain events from Discord.
# MESSAGE_CONTENT is required to read message content.
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True # Required for voice functionality

# Initialize the bot
bot = commands.Bot(command_prefix='!', intents=intents)

# Initialize Spotipy with client credentials for searching
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=SPOTIPY_CLIENT_ID,
    client_secret=SPOTIPY_CLIENT_SECRET
))

# --- Bot Events ---
@bot.event
async def on_ready():
    """
    Event that fires when the bot successfully connects to Discord.
    """
    print(f'Logged in as {bot.user.name} ({bot.user.id})')
    print('------')

# --- Bot Commands ---
@bot.command(name='suggest')
async def suggest_song(ctx, *, song_name: str):
    """
    Suggests songs from Spotify based on the provided song name.
    Usage: !suggest <song name>
    """
    if not SPOTIPY_CLIENT_ID or not SPOTIPY_CLIENT_SECRET:
        await ctx.send("Spotify API credentials are not set up. Please configure SPOTIPY_CLIENT_ID and SPOTIPY_CLIENT_SECRET environment variables.")
        return

    try:
        # Search for tracks on Spotify
        results = sp.search(q=song_name, type='track', limit=5)
        tracks = results['tracks']['items']

        if not tracks:
            await ctx.send(f"Sorry, I couldn't find any songs matching '{song_name}' on Spotify.")
            return

        embed = discord.Embed(
            title=f"Spotify Song Suggestions for '{song_name}'",
            color=0x1DB954 # Spotify green color
        )

        for i, track in enumerate(tracks):
            track_name = track['name']
            artist_name = track['artists'][0]['name']
            track_url = track['external_urls']['spotify']
            embed.add_field(
                name=f"{i+1}. {track_name} by {artist_name}",
                value=f"[Listen on Spotify]({track_url})",
                inline=False
            )
        await ctx.send(embed=embed)

    except Exception as e:
        await ctx.send(f"An error occurred while searching for songs: {e}")

@bot.command(name='play')
async def play_song(ctx, *, song_name: str):
    """
    Plays a song in the voice channel the user is currently in.
    Searches YouTube for the song and streams its audio.
    Usage: !play <song name>
    """
    # Check if the user is in a voice channel
    if not ctx.author.voice:
        await ctx.send("You need to be in a voice channel to use this command!")
        return

    channel = ctx.author.voice.channel
    voice_client = ctx.voice_client

    # If bot is not in a voice channel, join the user's channel
    if voice_client is None:
        try:
            voice_client = await channel.connect()
            await ctx.send(f"Joined voice channel: **{channel.name}**")
        except discord.ClientException:
            await ctx.send("I am already in a voice channel.")
            return
        except asyncio.TimeoutError:
            await ctx.send("Could not connect to the voice channel. Timeout.")
            return
    elif voice_client.channel != channel:
        # If bot is in a different channel, move to the user's channel
        await voice_client.move_to(channel)
        await ctx.send(f"Moved to voice channel: **{channel.name}**")

    # Stop any currently playing audio
    if voice_client.is_playing():
        voice_client.stop()

    await ctx.send(f"Searching for '{song_name}' on YouTube...")

    try:
        # Use yt-dlp to get the audio stream URL
        ydl_opts = {
            'format': 'bestaudio/best',
            'noplaylist': True,
            'default_search': 'ytsearch', # Search YouTube by default
            'quiet': True, # Suppress console output
            'extract_flat': 'in_playlist', # For faster search
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(song_name, download=False)
            if 'entries' in info:
                # Take the first result from the search
                video_info = info['entries'][0]
            else:
                video_info = info # Direct video if exact URL/ID was given

            audio_url = video_info['url']
            title = video_info.get('title', 'Unknown Title')
            uploader = video_info.get('uploader', 'Unknown Uploader')

        # Play the audio stream using FFmpeg
        # FFmpegOpusAudio is optimized for Discord voice
        voice_client.play(discord.FFmpegOpusAudio(audio_url, before_options='-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'))
        await ctx.send(f"Now playing: **{title}** by **{uploader}**")

    except Exception as e:
        await ctx.send(f"An error occurred while trying to play the song: {e}. Make sure `ffmpeg` is installed and accessible.")
        print(f"Error playing song: {e}")

@bot.command(name='stop')
async def stop_playing(ctx):
    """
    Stops the currently playing song and disconnects the bot from the voice channel.
    Usage: !stop
    """
    voice_client = ctx.voice_client
    if voice_client and voice_client.is_playing():
        voice_client.stop()
        await ctx.send("Stopped playing.")
    if voice_client:
        await voice_client.disconnect()
        await ctx.send("Disconnected from voice channel.")
    else:
        await ctx.send("I am not currently in a voice channel.")

# Run the bot
if __name__ == '__main__':
    if not DISCORD_BOT_TOKEN:
        print("Error: DISCORD_BOT_TOKEN environment variable not set.")
        print("Please set it before running the bot.")
    else:
        bot.run(DISCORD_BOT_TOKEN)

