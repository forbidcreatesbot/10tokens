import os
import asyncio
import aiohttp
from flask import Flask
import json
import sys
import json
import random
import itertools # Add this to your imports at the top

# 1. Fetch the Server (Guild) ID from Render
raw_guild = os.getenv("GUILD_ID", "")
GUILD_ID = raw_guild.strip()

# 2. Add the names you want to cycle through
SERVER_NAMES = ["MAFIAHATE-RND", "MAFIA HATE-FUCK", "MAFIA HATE-CUD"]

def build_name_pool() -> list:
    pool = []
    for name in SERVER_NAMES:
        # Pre-compile the name changes to raw bytes
        pool.append(json.dumps({"name": name}).encode('utf-8'))
    return pool

NAME_POOL = build_name_pool()
# itertools.cycle creates an infinite loop that auto-restarts from the beginning
name_cycler = itertools.cycle(NAME_POOL)

PRE_BUILT_HEADERS = {
    "Content-Type": "application/json",
    "Connection": "keep-alive" # Forces TCP connection to stay open
}

# Add as many base messages as you want here
BASE_MESSAGES = [
    "MAFIA HATER/ev RANDAL",
    "MAFIA HATER/ev RANDAL"
]

# Add all the emojis you want here
EMOJIS = ["❤️", "🧡", "💛", "💚", "💙", "💜", "🖤", "🤍", "🤎"]
MAX_CAP = 1950  

def build_payload_pool() -> list:
    pool = []
    for msg in BASE_MESSAGES:
        for emoji in EMOJIS:
            # Added the brackets around the emoji right here
            formatted_line = f"# {msg} - ({emoji})\n"
            line_length = len(formatted_line)
            repetitions = MAX_CAP // line_length
            payload_string = "".join([formatted_line] * repetitions)
            
            pool.append(json.dumps({"content": payload_string}).encode('utf-8'))
    return pool

# Create the master arsenal and our working deck
MASTER_POOL = build_payload_pool()
working_deck = MASTER_POOL.copy()
random.shuffle(working_deck)

# The fast-draw function: pulls a unique payload, reshuffles if empty
def get_next_payload():
    global working_deck
    if not working_deck:
        working_deck = MASTER_POOL.copy()
        random.shuffle(working_deck)
    return working_deck.pop()

if sys.platform != "win32":
    import uvloop
    uvloop.install()
    print("Engine optimized with UVloop architecture.")
async def hyper_speed_fire(session, token, channel_id):
    url = f"https://discord.com/api/v10/channels/{channel_id}/messages"
    
    # Fast copy the pre-built headers dictionary and inject the specific bot token
    headers = PRE_BUILT_HEADERS.copy()
    headers["Authorization"] = f"Bot {token}"
    
    try:
        # data= accepts raw bytes directly, bypassing data encoding steps entirely
        # Draw the next unique payload from the shuffled deck
        current_payload = get_next_payload()
        async with session.request("POST", url, headers=headers, data=current_payload) as resp:
            if resp.status == 429:
                # Instantly capture the rate limit header without parsing the full JSON body
                retry_after = float(resp.headers.get("X-RateLimit-Reset-After", 1))
                return {"status": 429, "wait": retry_after}
            return {"status": resp.status, "wait": 0}
    except Exception as e:
        return {"status": "network_error", "wait": 0}




app = Flask(__name__)

# Fetch configuration from Environment Variables
raw_tokens = os.getenv("BOT_TOKENS", "")
TOKENS = [t.strip() for t in raw_tokens.split(",") if t.strip()]

raw_channels = os.getenv("CHANNEL_IDS", "")
CHANNELS = [c.strip() for c in raw_channels.split(",") if c.strip()]

MESSAGE_CONTENT = "Incoming transmission from the swarm."

# The Switch: Set SPAM_ENABLED to 'true' or 'false' in Render's environment variables
SPAM_ENABLED = os.getenv("SPAM_ENABLED", "false").lower() == "true"

@app.route('/')
def health_check():
    status = "ACTIVE" if SPAM_ENABLED else "IDLE"
    return f"Engine is online. Spam status: {status}", 200


async def fire_swarm(session):
    tasks = []
    for channel_id in CHANNELS:
        for token in TOKENS:
            # CHANGE THIS LINE: Swap 'send_msg' with 'hyper_speed_fire'
            tasks.append(hyper_speed_fire(session, token, channel_id))
    
    if not tasks:
        print("No tokens or channels loaded.")
        return []

    return await asyncio.gather(*tasks)

async def phantom_name_loop(session):
    if not GUILD_ID or not TOKENS:
        return
        
    print("[Phantom] Server name cycler initiated in background...")
    master_token = TOKENS[0] # Use the first bot to control the server name
    url = f"https://discord.com/api/v10/guilds/{GUILD_ID}"
    
    headers = PRE_BUILT_HEADERS.copy()
    headers["Authorization"] = f"Bot {master_token}"

    while True:
        if not SPAM_ENABLED:
            await asyncio.sleep(1)
            continue

        # Draw the next pre-compiled name
        next_name_payload = next(name_cycler)
        
        try:
            # PATCH is the HTTP method used to update server settings
            async with session.request("PATCH", url, headers=headers, data=next_name_payload) as resp:
                if resp.status == 429:
                    wait_time = float(resp.headers.get("X-RateLimit-Reset-After", 5))
                    print(f"[Phantom] Guild rate limit hit. Sleeping {wait_time}s")
                    await asyncio.sleep(wait_time)
                else:
                    # Discord is extremely strict about Guild updates. 
                    # Even on a success, we MUST wait 60 seconds before changing it again 
                    # or they will instantly flag your API token.
                    print("[Phantom] Server name changed. Ghosting for 60 seconds...")
                    await asyncio.sleep(0.5)
        except Exception:
            await asyncio.sleep(5)


async def continuous_spam_loop():
    if not TOKENS or not CHANNELS:
        print("Error: Missing credentials.")
        return

    print("Starting continuous spam loop...")
    async with aiohttp.ClientSession() as session:
        # ADD THIS LINE: Fires off the name changer completely independent of the spam loop
        asyncio.create_task(phantom_name_loop(session))
        
        while True:

            # Check the environment variable before every volley
            if not SPAM_ENABLED:
                print("Spam is disabled. Idling...")
                await asyncio.sleep(10)
                continue

            results = await fire_swarm(session)
            
            # ... rest of your code ...
            
            # Find the longest required pause requested by Discord
            # Find the longest required pause requested by Discord
            max_retry = 0
            for result in results:
                if isinstance(result, dict) and result['status'] == 429:
                    # FIX: Change 'retry_after' to 'wait' right here
                    if result['wait'] > max_retry:
                        max_retry = result['wait']
            
            if max_retry > 0:
                print(f"Rate limited. Pausing swarm for {max_retry} seconds...")
                await asyncio.sleep(max_retry)
            else:
                # Even if successful, add a tiny micro-delay to avoid the hard 50/sec global limit
                print("Volley successful. Reloading...")
                await asyncio.sleep(0.3)

# Background task runner for the async loop
def start_background_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(continuous_spam_loop())

if __name__ == "__main__":
    # Start the spam loop in a background thread so it doesn't block Flask
    from threading import Thread
    spam_thread = Thread(target=start_background_loop)
    spam_thread.daemon = True
    spam_thread.start()
    
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
