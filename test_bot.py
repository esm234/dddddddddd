#!/usr/bin/env python3
"""
Test script for the Telegram bot
"""

import os
import sys

# Set the bot token
os.environ['BOT_TOKEN'] = '7936685638:AAEoXoyLbdH6aYpVI6M4WXhCai4_fJ8vs-0'

try:
    from bot import main
    print("✅ Bot is ready to start!")
    print("🔗 Bot Token: 7936685638:AAEoXoyLbdH6aYpVI6M4WXhCai4_fJ8vs-0")
    print("📱 You can now test the bot on Telegram")
    print("🚀 Starting bot...")
    main()
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
