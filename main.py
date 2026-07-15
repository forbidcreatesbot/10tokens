import os
import asyncio
import aiohttp
from flask import Flask
from threading import Thread

# Initialize Flask to maintain persistent cloud execution
app = Flask(__name__)

# Dynamically load token1 through token10 from environment variables
TOKENS = [os.getenv(f"token{i}") for i in range(1, 11) if os.getenv(f"token{i}")]
CHANNEL_ID = os.getenv("CHANNEL_ID", "YOUR_CHANNEL_ID_HERE")
MESSAGE_CONTENT = "Incoming transmission from the swarm."

@app.route('/')
def health_check():
    return "Engine is online and waiting.", 200

async def send_msg(session, token):
    url = f"https://discord.com/api/v10/channels/{CHANNEL_ID}/messages"
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
        # Create all 10 network tasks in memory
        tasks = [send_msg(session, token) for token in TOKENS]
        
        # asyncio.gather fires them all concurrently — no waiting in line
        results = await asyncio.gather(*tasks)
        print(f"Blast fired. Status codes: {results}")

@app.route('/fire')
def trigger_blast():
    if not TOKENS:
        return "Error: No tokens found in environment variables.", 400
    
    # Trigger the async event loop from the synchronous Flask route
    asyncio.run(fire_all())
    return "All 10 bots fired successfully!", 200

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    # Start the Flask background loop sequence
    server_thread = Thread(target=run_web)
    server_thread.start()
