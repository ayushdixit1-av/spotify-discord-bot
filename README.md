Discord Spotify Bot
A Discord bot that can suggest songs from Spotify and play music from YouTube in a voice channel.

Features
Song Suggestions: Get Spotify song suggestions by name using a slash command.

Interactive Play Music: Search for music, get suggestions, and select a song to play in a Discord voice channel using a slash command.

Stop Music: Stop currently playing music and disconnect the bot using a slash command.

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

Under "Scopes", select bot and applications.commands. (The applications.commands scope is crucial for slash commands).

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
Ensure the following files are in the root of your project directory:

bot.py: The updated Python code for your bot (provided above).

requirements.txt:

discord.py[voice]
spotipy
yt-dlp

Procfile:

start: python bot.py

runtime.txt: (Recommended for explicit Python version)

python-3.9.18

4. Deploy on Railway
Create a Git Repository: Initialize a Git repository in your project folder and push all the above files to a GitHub repository.

Deploy to Railway:

Go to your Railway Dashboard.

Click "New Project" and select "Deploy from Git Repo".

Connect your GitHub account and select the repository.

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

Bot Commands (Slash Commands)
Once the bot is online in your Discord server:

/suggest <song_name>: Get Spotify song suggestions.

Example: Type /suggest and then enter Hotel California in the song_name field.

/play <search_query>: Search for songs, get suggestions, and then reply with the number of the song you want to play to play it in your voice channel.

Example: Type /play and then enter Despacito in the search_query field.

/stop: Stop the current song and disconnect the bot from the voice channel.

Troubleshooting
If you encounter issues during deployment, especially "Nixpacks was unable to generate a build plan for this app," consider the following:

Verify File Presence and Location:

Ensure bot.py, requirements.txt, Procfile, and runtime.txt are all present in the root directory of your GitHub repository.

Correct Filenames:

Ensure requirements.txt (with 's') and Procfile (capital 'P') are spelled correctly.

Procfile Line Endings (CRITICAL):

The Procfile must use Unix-style line endings (LF), not Windows-style (CRLF). Use a code editor (VS Code, Notepad++, Sublime Text) to convert and save.

Empty requirements.txt:

Ensure your requirements.txt file is not empty and correctly lists all dependencies.

Check Railway Build Logs:

View the "Deployments" tab on Railway for specific error messages.

Typos:

Double-check for any typos in filenames or content.

Clean Redeploy:

Consider deleting the Railway service and redeploying from scratch if persistent issues occur.
