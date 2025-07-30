Discord Spotify Bot
A Discord bot that can suggest songs from Spotify and play music from YouTube in a voice channel.

Features
Song Suggestions: Get Spotify song suggestions by name using a slash command.

Play Music: Play music in a Discord voice channel by providing a song name, Spotify track URL, or YouTube URL.

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

bot.py: The updated Python code for your bot (provided above, now relying on FFMPEG_PATH environment variable).

requirements.txt: (UPDATED - imageio-ffmpeg removed)

discord.py[voice]
spotipy
yt-dlp

Procfile:

start: python bot.py

runtime.txt: (Recommended for explicit Python version)

python-3.9.18

nixpacks.toml: (UPDATED - simplified to only install ffmpeg via apt)

[phases.setup]
apt_packages = ["ffmpeg"]

Note: The start.sh file is no longer needed and should be removed from your repository.

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

FFMPEG_PATH: /usr/bin/ffmpeg (This environment variable tells discord.py where to find FFmpeg after it's installed by apt)

Railway will automatically redeploy your application after you add these variables.

Bot Commands (Slash Commands)
Once the bot is online in your Discord server:

/suggest <song_name>: Get Spotify song suggestions.

Example: Type /suggest and then enter Hotel California in the song_name field.

/play <query>: Plays a song. You can provide a song name, a Spotify track URL, or a YouTube URL.

Example (Song Name): Type /play and then enter Despacito in the query field.

Example (YouTube URL): Type /play and then enter a YouTube video URL (e.g., https://www.youtube.com/watch?v=dQw4w9WgXcQ).

Example (Spotify Track URL): Type /play and then enter a Spotify track URL (e.g., https://open.spotify.com/track/7qiZfU4dY1lWllzX7K8Wp6).

/stop: Stop the current song and disconnect the bot from the voice channel.

Troubleshooting
If you encounter issues during deployment, especially "Nixpacks was unable to generate a build plan for this app," consider the following:

Verify File Presence and Location:

Ensure bot.py, requirements.txt, Procfile, runtime.txt, and nixpacks.toml are all present in the root directory of your GitHub repository.

Correct Filenames:

Ensure requirements.txt (with 's'), Procfile (capital 'P'), and nixpacks.toml are spelled correctly.

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

No Voice Output / Audio Issues:

Check Railway Runtime Logs: After the bot deploys and starts, go to the "Logs" tab for your service on Railway. When you try to play a song, look for any errors or warnings that appear. These runtime errors are crucial for diagnosing audio playback problems.

Bot Permissions in Discord: Double-check that your bot has the "Connect" and "Speak" permissions in the specific voice channel you are trying to use it in. Even if it joins, lacking "Speak" permission will prevent audio.

Discord Server Region/Voice Settings: While rare, ensure there are no unusual voice region settings on your Discord server that might interfere with bot audio.

Audio Source Compatibility: Although yt-dlp is robust, very occasionally, a specific YouTube video's audio format might cause issues. Try playing different songs to see if it's a consistent problem or isolated to certain tracks.

Opus Library: discord.py relies on the Opus audio codec for voice. While discord.py[voice] attempts to install necessary bindings (PyNaCl), sometimes the underlying Opus library might be missing or incompatible. If the Railway logs show issues related to opus or PyNaCl during installation, that's a strong indicator. This is why we are now relying on apt_packages = ["ffmpeg"] and FFMPEG_PATH.
