#!/bin/bash

# Explicitly add common ffmpeg installation paths to the PATH
# This ensures discord.py can find the ffmpeg executable
export PATH=$PATH:/usr/bin:/usr/local/bin:/usr/local/sbin:/usr/sbin:/sbin

# Execute the Python bot
python bot.py
