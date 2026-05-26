import os
import discord
from dotenv import load_dotenv
import asyncio

load_dotenv()

TOKEN = os.getenv('DISCORD_BOT_TOKEN')
CHANNEL_ID = os.getenv('DISCORD_CHANNEL_ID')

intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)

# This will hold a callback function to trigger tasks
trigger_callback = None

def set_trigger_callback(callback):
    global trigger_callback
    trigger_callback = callback

@bot.event
async def on_ready():
    print(f'[Discord] Logged in as {bot.user}')

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # Check if the message is in the target channel
    if CHANNEL_ID and str(message.channel.id) == CHANNEL_ID:
        content = message.content.lower()
        print(f"[Discord] Received message in monitored channel: {content}")
        
        # Super basic parser: looking for a keyword like "drop" or "sku:"
        # Real logic would extract URLs or specific SKUs
        if "sku:" in content:
            # Example message: "sku: 12345 site: target"
            parts = content.split()
            sku = None
            site = "target" # default
            for i, part in enumerate(parts):
                if part == "sku:" and i + 1 < len(parts):
                    sku = parts[i+1]
                if part == "site:" and i + 1 < len(parts):
                    site = parts[i+1]
            
            if sku and trigger_callback:
                print(f"[Discord] Triggering drop for SKU {sku} on {site}")
                # We schedule the callback safely in the event loop
                asyncio.create_task(trigger_callback(sku, site))
                
        elif content.startswith("enter"):
            parts = content.split()
            if len(parts) >= 2:
                try:
                    task_id = int(parts[1])
                    import requests
                    res = requests.post(f"http://localhost:8000/tasks/{task_id}/input?input_text=enter")
                    if res.status_code == 200:
                        await message.channel.send(f"✅ Sent enter keystroke to Task {task_id}")
                    else:
                        await message.channel.send(f"❌ Failed to send enter: Task might not be running.")
                except Exception as e:
                    await message.channel.send(f"❌ Error: {e}")
        
        elif content.startswith('stop '):
            import requests
            parts = content.split()
            if len(parts) != 2:
                await message.channel.send("Invalid format. Use: `stop <task_id>`")
                return
            
            task_id = parts[1]
            try:
                res = requests.post(f"http://localhost:8000/tasks/{task_id}/stop")
            except Exception as e:
                await message.channel.send(f"❌ Failed to reach backend: {str(e)}")
                return
                
            if res.status_code == 200:
                await message.channel.send(f"⏹️ Stopped Task {task_id}")
                requests.post(f"http://localhost:8000/tasks/{task_id}/log", json={}, params={"message": f"Task stopped manually via Discord", "level": "info"})
            else:
                await message.channel.send(f"⚠️ Failed to stop Task {task_id}. It might not be running.")

async def start_discord_bot():
    if not TOKEN:
        print("[Discord] No bot token found. Listener will not start.")
        return
    await bot.start(TOKEN)
