import os
import asyncio
import aiohttp
from flask import Flask
from threading import Thread

app = Flask(__name__)

# 1. Fetch and split the comma-separated environment variables
# Example format in Render: "token1,token2,token3"
raw_tokens = os.getenv("BOT_TOKENS", "")
TOKENS = [t.strip() for t in raw_tokens.split(",") if t.strip()]

# Example format in Render: "channel1,channel2"
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
        # Stateless POST: Zero websocket bandwidth consumed
        async with session.post(url, headers=headers, json=payload) as response:
            return response.status
    except Exception as e:
        return str(e)

async def fire_all():
    # Opening a single session for all requests drastically reduces overhead
    async with aiohttp.ClientSession() as session:
        tasks = []
        
        # Loop through every channel and every token to build the strike package
        for channel_id in CHANNELS:
            for token in TOKENS:
                tasks.append(send_msg(session, token, channel_id))
        
        if not tasks:
            print("Error: No tokens or channels loaded.")
            return

        # asyncio.gather fires them all concurrently — no waiting in line
        results = await asyncio.gather(*tasks)
        print(f"Blast fired. Status codes: {results}")

@app.route('/fire')
def trigger_blast():
    if not TOKENS or not CHANNELS:
        return "Error: Missing BOT_TOKENS or CHANNEL_IDS in environment variables.", 400
    
    # Trigger the async event loop from the synchronous Flask route
    asyncio.run(fire_all())
    return f"Fired {len(TOKENS)} bots into {len(CHANNELS)} channels!", 200

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    # Start the Flask background loop sequence
    server_thread = Thread(target=run_web)
    server_thread.start()
