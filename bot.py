import os
import discord
from discord.ext import commands
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import asyncio
import yt_dlp # For fetching audio from YouTube
import re # For regular expressions to check URLs

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

# Initialize the bot without a command prefix for slash commands
# Keeping a fallback prefix for testing, but main usage is slash commands
bot = commands.Bot(command_prefix=commands.when_mentioned_or("!"), intents=intents) 

# Initialize Spotipy with client credentials for searching
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=SPOTIPY_CLIENT_ID,
    client_secret=SPOTIPY_CLIENT_SECRET
))

# Regex for YouTube and Spotify URLs
YOUTUBE_URL_REGEX = r"(?:https?://)?(?:www\.)?(?:youtube\.com|youtu\.be)/(?:watch\?v=|embed/|v/|)([\w-]{11})(?:\S+)?"
SPOTIFY_TRACK_URL_REGEX = r"https?://open\.spotify\.com/track/([a-zA-Z0-9]+)(?:\?.*)?"

# --- Bot Events ---
@bot.event
async def on_ready():
    """
    Event that fires when the bot successfully connects to Discord.
    Synchronizes slash commands.
    """
    print(f'Logged in as {bot.user.name} ({bot.user.id})')
    print('------')
    try:
        # Sync slash commands globally (or to specific guilds for faster testing)
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Error syncing commands: {e}")

# --- Helper Function for Playing Audio ---
async def play_audio_from_youtube(interaction: discord.Interaction, source_query: str, is_url: bool = False):
    """
    Helper function to search YouTube and play audio in a voice channel.
    Can take a search query or a direct YouTube URL.
    """
    await interaction.followup.send(f"Preparing to play: '{source_query}'...")

    try:
        ydl_opts = {
            'format': 'bestaudio/best',
            'noplaylist': True,
            'quiet': True, # Suppress console output
            'extract_flat': 'in_playlist', # For faster search
        }

        if not is_url:
            ydl_opts['default_search'] = 'ytsearch' # Search YouTube if not a direct URL

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(source_query, download=False)
            
            # If it's a search result, take the first entry
            if 'entries' in info and info['entries']:
                video_info = info['entries'][0]
            elif 'url' in info: # Direct video if exact URL/ID was given
                video_info = info
            else:
                await interaction.followup.send(f"Could not find any playable audio for '{source_query}'.")
                return

            audio_url = video_info['url']
            title = video_info.get('title', 'Unknown Title')
            uploader = video_info.get('uploader', 'Unknown Uploader')

        # Get voice client from interaction's guild
        voice_client = interaction.guild.voice_client
        if voice_client:
            # Explicitly provide the path to the ffmpeg executable
            voice_client.play(discord.FFmpegOpusAudio(audio_url, executable='/usr/bin/ffmpeg', before_options='-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'))
            await interaction.followup.send(f"Now playing: **{title}** by **{uploader}**")
        else:
            await interaction.followup.send("I am not in a voice channel. Please use `/play` while I am connected.")


    except Exception as e:
        await interaction.followup.send(f"An error occurred while trying to play the song: {e}. Make sure `ffmpeg` is installed and accessible.")
        print(f"Error playing song: {e}")

# --- Bot Commands (Slash Commands) ---
@bot.tree.command(name="suggest", description="Suggests songs from Spotify based on your query.")
@discord.app_commands.describe(song_name="The name of the song to search for.")
async def suggest_song(interaction: discord.Interaction, song_name: str):
    """
    Suggests songs from Spotify based on the provided song name.
    Usage: /suggest <song_name>
    """
    await interaction.response.defer() # Acknowledge the interaction immediately

    if not SPOTIPY_CLIENT_ID or not SPOTIPY_CLIENT_SECRET:
        await interaction.followup.send("Spotify API credentials are not set up. Please configure SPOTIPY_CLIENT_ID and SPOTIPY_CLIENT_SECRET environment variables.")
        return

    try:
        results = sp.search(q=song_name, type='track', limit=5)
        tracks = results['tracks']['items']

        if not tracks:
            await interaction.followup.send(f"Sorry, I couldn't find any songs matching '{song_name}' on Spotify.")
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
        await interaction.followup.send(embed=embed)

    except Exception as e:
        await interaction.followup.send(f"An error occurred while searching for songs: {e}")


@bot.tree.command(name="play", description="Plays a song from Spotify/YouTube. Provide a name or URL.")
@discord.app_commands.describe(query="The song name, Spotify track URL, or YouTube URL to play.")
async def play_song(interaction: discord.Interaction, query: str):
    """
    Plays a song in the voice channel.
    If a Spotify or YouTube URL is provided, it attempts to play directly.
    Otherwise, it searches Spotify and plays the top result.
    Usage: /play <song name or URL>
    """
    await interaction.response.defer() # Acknowledge the interaction immediately

    # Check if the user is in a voice channel
    if not interaction.user.voice:
        await interaction.followup.send("You need to be in a voice channel to use this command!")
        return

    channel = interaction.user.voice.channel
    voice_client = interaction.guild.voice_client

    # If bot is not in a voice channel, join the user's channel
    if voice_client is None:
        try:
            voice_client = await channel.connect()
            await interaction.followup.send(f"Joined voice channel: **{channel.name}**")
        except discord.ClientException:
            await interaction.followup.send("I am already in a voice channel.")
            return
        except asyncio.TimeoutError:
            await interaction.followup.send("Could not connect to the voice channel. Timeout.")
            return
    elif voice_client.channel != channel:
        # If bot is in a different channel, move to the user's channel
        await voice_client.move_to(channel)
        await interaction.followup.send(f"Moved to voice channel: **{channel.name}**")

    # Check for Spotify API credentials for Spotify search/URL parsing
    if not SPOTIPY_CLIENT_ID or not SPOTIPY_CLIENT_SECRET:
        await interaction.followup.send("Spotify API credentials are not set up. Please configure SPOTIPY_CLIENT_ID and SPOTIPY_CLIENT_SECRET environment variables.")
        return

    spotify_match = re.match(SPOTIFY_TRACK_URL_REGEX, query)
    youtube_match = re.match(YOUTUBE_URL_REGEX, query)

    if spotify_match:
        try:
            track_id = spotify_match.group(1)
            track_info = sp.track(track_id)
            song_name_for_youtube = f"{track_info['name']} {track_info['artists'][0]['name']}"
            await play_audio_from_youtube(interaction, song_name_for_youtube, is_url=False) # Search YouTube with Spotify track info
        except Exception as e:
            await interaction.followup.send(f"Could not retrieve Spotify track info or play: {e}")
    elif youtube_match:
        await play_audio_from_youtube(interaction, query, is_url=True) # Play YouTube URL directly
    else:
        # If not a URL, search Spotify and play the top result
        try:
            results = sp.search(q=query, type='track', limit=1)
            tracks = results['tracks']['items']

            if not tracks:
                await interaction.followup.send(f"Sorry, I couldn't find any songs matching '{query}' on Spotify.")
                return

            top_track = tracks[0]
            song_name_for_youtube = f"{top_track['name']} {top_track['artists'][0]['name']}"
            await play_audio_from_youtube(interaction, song_name_for_youtube, is_url=False) # Search YouTube with top Spotify result

        except Exception as e:
            await interaction.followup.send(f"An error occurred during the song search: {e}")


@bot.tree.command(name="stop", description="Stops the current song and disconnects the bot.")
async def stop_playing(interaction: discord.Interaction, ):
    """
    Stops the currently playing song and disconnects the bot from the voice channel.
    Usage: /stop
    """
    await interaction.response.defer() # Acknowledge the interaction immediately

    voice_client = interaction.guild.voice_client
    if voice_client and voice_client.is_playing():
        voice_client.stop()
        await interaction.followup.send("Stopped playing.")
    if voice_client:
        await voice_client.disconnect()
        await interaction.followup.send("Disconnected from voice channel.")
    else:
        await interaction.followup.send("I am not currently in a voice channel.")

# Run the bot
if __name__ == '__main__':
    if not DISCORD_BOT_TOKEN:
        print("Error: DISCORD_BOT_TOKEN environment variable not set.")
        print("Please set it before running the bot.")
    else:
        bot.run(DISCORD_BOT_TOKEN)

