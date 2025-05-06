from pyrogram import Client , filters
from var import *
from helper import *
import os , sys
import aiohttp , base64 , re
from urllib.parse import urlparse

async def update_github_file(repo_url: str, branch: str, file_name: str, new_content: str):
    parsed_url = urlparse(repo_url)
    token = re.search(r"ghp_\w+", parsed_url.netloc).group(0)
    repo_parts = parsed_url.path.strip("/").split("/")
    repo_owner, repo_name = repo_parts[0], repo_parts[1]

    file_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/{file_name}"
    headers = {"Authorization": f"token {token}"}

    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(file_url, params={"ref": branch}) as response:
            if response.status != 200:
                print(f"Error fetching file: {response.status}")
                return False
            
            file_data = await response.json()
            file_sha = file_data["sha"] 
            print(f"Current file content retrieved successfully. SHA: {file_sha}")

        new_content_encoded = base64.b64encode(new_content.encode("utf-8")).decode("utf-8")
        payload = {
            "message": f"Updating {file_name} via API",
            "content": new_content_encoded,
            "branch": branch,
            "sha": file_sha,
        }
        async with session.put(file_url, json=payload) as response:
            if response.status == 200:
                print(f"File updated successfully: {file_name}")
                return True
            else:
                print(f"Error updating file: {response.status}")
                return False

@Client.on_message(filters.private & filters.command('change') & filters.user(OWNER))
async def change(app , message):
    if not CURRENT_REPO or not CURRENT_BRANCH:
        return await replyMessage(message , '**Fill Up CURRENT_REPO & CURRENT_BRANCH First !**')
    try:
        key , value =[ i.strip() for i in message.text.split(maxsplit=1)[1].strip().split('=' , maxsplit=1 ) ]
    except:
        return await replyMessage(message , '**Send Correctly In Format Like `/change FSUB = "-100xx -100xx"`**')
    with open("config.env", "r") as file:
        lines = file.readlines()
    status = None
    with open("config.env", "w") as file:
        for line in lines:
            if line.split("=" , maxsplit=1)[0].strip() == key:
                file.write(f"{key} = {value}\n")
                status = True
            else:
                file.write(line)
    if not status: return await replyMessage(message , '**`No Such Variable Found !`**')
    with open("config.env", "r") as file:
        lines = file.read()
    status = await update_github_file(CURRENT_REPO , CURRENT_BRANCH , 'config.env' , lines)
    msg = await replyMessage(message , f'`Succesfully Changed {key} = {value}, Now Restarting !`')
    with open(".restartmsg", "w") as f:
        f.write(f"{msg.chat.id}\n{msg.id}\n")
    os.execl(sys.executable, sys.executable, '-B' , "main.py")
