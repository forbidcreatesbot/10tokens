import os
import asyncio
import aiohttp
from flask import Flask
from threading import Thread

app = Flask(__name__)

raw_tokens = os.getenv("BOT_TOKENS", "")
TOKENS = [t.strip() for t in raw_tokens.split(",") if t.strip()]

raw_channels = os.getenv("CHANNEL_IDS", "")
CHANNELS = [c.strip() for c in raw_channels.split(",") if c.strip()]

MESSAGE_CONTENT = "Incoming transmission from the swarm."

@app.route('/')
def health_check():
    return "Engine is online and waiting.", 200

async def send_msg(session, token, channel_id):
    url = f"https://discord.com/api/v10/channels/{channel_id}/messages"
    headers = {
        "Authorization": f"Bot {token}",
        "Content-Type": "application/json"
    }
    payload = {"content": MESSAGE_CONTENT}
    
    try:
        async with session.post(url, headers=headers, json=payload) as response:
            return response.status
    except Exception as e:
        return str(e)

async def fire_all():
    async with aiohttp.ClientSession() as session:
        tasks = []
        for channel_id in CHANNELS:
            for token in TOKENS:
                tasks.append(send_msg(session, token, channel_id))
        
        if not tasks:
            return "No tokens or channels loaded."

        # Wait for all bots to fire, then return the list of status codes
        results = await asyncio.gather(*tasks)
        return results

@app.route('/fire')
def trigger_blast():
    if not TOKENS or not CHANNELS:
        return "Error: Missing BOT_TOKENS or CHANNEL_IDS in environment variables.", 400
    
    # Run the blast and capture the status codes
    codes = asyncio.run(fire_all())
    
    # Show the codes directly on the webpage
    return f"Blast fired! Discord returned these status codes: {codes}", 200

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    server_thread = Thread(target=run_web)
    server_thread.start()
