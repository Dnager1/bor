#!/bin/bash
# Quick Start Script for Discord Bot
# Run this script to start the bot

echo "========================================"
echo "  Discord Bot - Quick Start"
echo "========================================"
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found!"
    echo ""
    echo "Please create a .env file with your bot token:"
    echo "  cp .env.example .env"
    echo "  Then edit .env and add your DISCORD_BOT_TOKEN and OWNER_ID"
    echo ""
    exit 1
fi

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed!"
    exit 1
fi

# Check if dependencies are installed
echo "📦 Checking dependencies..."
python3 -c "import discord" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "📦 Installing dependencies..."
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "❌ Error: Failed to install dependencies"
        exit 1
    fi
fi

echo "✅ Dependencies OK"
echo ""

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p data/backups
mkdir -p logs
echo "✅ Directories created"
echo ""

# Start the bot
echo "🚀 Starting Discord Bot..."
echo "========================================"
echo ""

python3 bot.py
