import os
import asyncio
import aiohttp
from flask import Flask
import json
import sys
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
        async with session.request("POST", url, headers=headers, data=PRE_COMPILED_BYTES) as resp:
            if resp.status == 429:
                # Instantly capture the rate limit header without parsing the full JSON body
                retry_after = float(resp.headers.get("X-RateLimit-Reset-After", 1))
                return {"status": 429, "wait": retry_after}
            return {"status": resp.status, "wait": 0}
    except Exception as e:
        return {"status": "network_error", "wait": 0}

# Pre-compile the exact payload to raw bytes ahead of time
raw_json_data = {"content": "Your optimized message"}
PRE_COMPILED_BYTES = json.dumps(raw_json_data).encode('utf-8')

# Pre-define fixed headers to avoid dynamic dictionary generation
PRE_BUILT_HEADERS = {
    "Content-Type": "application/json",
    "Connection": "keep-alive" # Forces TCP connection to stay open
}

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

async def send_msg(session, token, channel_id):
    url = f"https://discord.com/api/v10/channels/{channel_id}/messages"
    headers = {
        "Authorization": f"Bot {token}",
        "Content-Type": "application/json"
    }
    payload = {"content": MESSAGE_CONTENT}
    
    try:
        async with session.post(url, headers=headers, json=payload) as response:
            if response.status == 429:
                # If rate limited, grab the exact wait time Discord demands
                rate_limit_data = await response.json()
                retry_after = rate_limit_data.get('retry_after', 1)
                return {'status': 429, 'retry_after': retry_after}
            return {'status': response.status, 'retry_after': 0}
    except Exception as e:
        return {'status': str(e), 'retry_after': 0}

# The base text string you want to repeat
BASE_TEXT = "testing for educational"

# Hard limitations defined by Discord's API structure
MAX_CAP = 1950  # Leaving a safety buffer short of the absolute 2000 limit

def build_max_payload(text: str) -> str:
    # Discord H1 requires an absolute newline block format: '# text\n'
    formatted_line = f"# {text}\n"
    line_length = len(formatted_line)
    
    # Calculate exactly how many full lines fit under the safety ceiling
    repetitions = MAX_CAP // line_length
    
    # Build the full payload via structural list multiplication
    payload = "".join([formatted_line] * repetitions)
    
    print(f"[Engine] Payload constructed. Total length: {len(payload)} chars across {repetitions} rows.")
    return payload

# Pre-compile the maximum density payload array into memory before loop entry
FINAL_MESSAGE_PAYLOAD = build_max_payload(BASE_TEXT)

async def fire_swarm(session):
    tasks = []
    for channel_id in CHANNELS:
        for token in TOKENS:
            tasks.append(send_msg(session, token, channel_id))
    
    if not tasks:
        print("No tokens or channels loaded.")
        return []

    # Fire all 10 simultaneously
    return await asyncio.gather(*tasks)

async def continuous_spam_loop():
    if not TOKENS or not CHANNELS:
        print("Error: Missing credentials.")
        return

    print("Starting continuous spam loop...")
    async with aiohttp.ClientSession() as session:
        while True:
            # Check the environment variable before every volley
            # To stop, you must restart the app after changing the variable in Render
            if not SPAM_ENABLED:
                print("Spam is disabled. Idling...")
                await asyncio.sleep(10)
                continue

            results = await fire_swarm(session)
            
            # Find the longest required pause requested by Discord
            max_retry = 0
            for result in results:
                if isinstance(result, dict) and result['status'] == 429:
                    if result['retry_after'] > max_retry:
                        max_retry = result['retry_after']
            
            if max_retry > 0:
                print(f"Rate limited. Pausing swarm for {max_retry} seconds...")
                await asyncio.sleep(max_retry)
            else:
                # Even if successful, add a tiny micro-delay to avoid the hard 50/sec global limit
                print("Volley successful. Reloading...")
                await asyncio.sleep(0.5)

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
