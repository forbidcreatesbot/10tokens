import os
import asyncio
import aiohttp
from flask import Flask

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

        results = await asyncio.gather(*tasks)
        return results

@app.route('/fire')
def trigger_blast():
    if not TOKENS or not CHANNELS:
        return "Error: Missing BOT_TOKENS or CHANNEL_IDS in environment variables.", 400
    
    # Create a fresh loop for this specific request to bypass the atexit bug
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    codes = loop.run_until_complete(fire_all())
    loop.close()
    
    return f"Blast fired! Discord returned these status codes: {codes}", 200

if __name__ == "__main__":
    # Run directly on the main thread so Python never shuts down
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
