
import asyncio
import random
import string
from telethon import TelegramClient, functions

# Fill these with your credentials from https://my.telegram.org
api_id = 123456       # <-- Replace with your API ID
api_hash = 'your_api_hash'  # <-- Replace with your API Hash

# Your current channel username (e.g., "mychannel123")
current_username = 'mychannelx'

client = TelegramClient('session', api_id, api_hash)

async def update_channel_link():
    await client.start()
    username = current_username

    while True:
        # Change the last character
        new_suffix = random.choice(string.ascii_lowercase + string.digits)
        new_username = username[:-1] + new_suffix

        try:
            result = await client(functions.channels.UpdateUsernameRequest(
                channel=username,
                username=new_username
            ))
            print(f"[SUCCESS] Updated channel username to: {new_username}")
            username = new_username
        except Exception as e:
            print(f"[ERROR] Could not update username: {e}")

        await asyncio.sleep(300)  # 5 minutes

with client:
    client.loop.run_until_complete(update_channel_link())
