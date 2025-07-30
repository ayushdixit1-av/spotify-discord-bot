Discord Spotify Bot
A Discord bot that can suggest songs from Spotify and play music from YouTube in a voice channel.

Features
Song Suggestions: Get Spotify song suggestions by name.

Play Music: Play music in a Discord voice channel by searching on YouTube.

Stop Music: Stop currently playing music and disconnect the bot.

Setup Instructions
1. Create a Discord Bot
Go to the Discord Developer Portal.

Click "New Application".

Give your application a name and click "Create".

Navigate to the "Bot" tab on the left sidebar.

Click "Add Bot" and confirm.

Under "Privileged Gateway Intents", enable MESSAGE CONTENT INTENT and SERVER MEMBERS INTENT.

Copy your Bot Token. Keep this token secret!

Go to the "OAuth2" -> "URL Generator" tab.

Under "Scopes", select bot.

Under "Bot Permissions", select the following:

View Channels

Send Messages

Read Message History

Connect

Speak

Copy the generated URL and paste it into your browser to invite the bot to your Discord server.

2. Create a Spotify Application
Go to the Spotify Developer Dashboard.

Click "Create an app".

Give your app a name and description, then click "Create".

You will see your Client ID and Client Secret. Copy these.

3. Prepare Files for Deployment
Create the following files in the root of your project directory:

bot.py: The Python code for your bot (provided in the previous response).

requirements.txt:

discord.py[voice]
spotipy
yt-dlp

Procfile:

worker: python bot.py

4. Deploy on Railway
Create a Git Repository: Initialize a Git repository in your project folder and push all the above files (bot.py, requirements.txt, Procfile) to a GitHub repository.

Deploy to Railway:

Go to your Railway Dashboard.

Click "New Project" and select "Deploy from Git Repo".

Connect your GitHub account and select the repository where you pushed your bot files.

Railway will automatically detect the Python project and start the build process.

Set Environment Variables:

Once your project is created on Railway, go to its settings.

Navigate to the "Variables" tab.

Add the following environment variables:

DISCORD_BOT_TOKEN: Your Discord bot token.

SPOTIPY_CLIENT_ID: Your Spotify API Client ID.

SPOTIPY_CLIENT_SECRET: Your Spotify API Client Secret.

Railway will automatically redeploy your application after you add these variables.

Note on FFmpeg: Railway's build environment typically includes ffmpeg. If you encounter issues with audio playback, ensure ffmpeg is properly installed and accessible within the Railway container.

Bot Commands
Once the bot is online in your Discord server:

!suggest <song name>: Get Spotify song suggestions.

Example: !suggest Hotel California

!play <song name>: Play a song in the voice channel you are currently in.

Example: !play Despacito

!stop: Stop the current song and disconnect the bot from the voice channel.
