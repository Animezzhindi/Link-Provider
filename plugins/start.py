from pyrogram import Client , filters
from var import *
from helper import *
from db import *
from datetime import datetime
import time
import random , string
import os
import asyncio
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated

async def handle_token(app , message , b64):
    user_id = str(message.from_user.id)
    if 'TOKEN' not in cf: cf['TOKEN'] = {}
    if user_id not in cf['TOKEN']: cf['TOKEN'][user_id] = {}
    token = cf['TOKEN'][user_id].get('TOKEN')
    tim = cf['TOKEN'][user_id].get('TIME')
    if (not tim) or ((int(time.time()) - tim) > 0 ):
        if token: 
            if not DOMAIN: link = f'https://telegram.me/{app.username}?start=token{token}'
            else: link = f'{DOMAIN}{token}'
        else:
            token = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(10))
            if not DOMAIN: link = f'https://telegram.me/{app.username}?start=token{token}'
            else: link = f'{DOMAIN}{token}'
            cf['TOKEN'][user_id]['TOKEN'] = token
        LOGGER(__name__).info(f'Token Generated For {message.from_user.first_name} - https://t.me/{app.username}?start=token{token}')
        short = await short_url(link)
        reply_markup = [
            [   
                InlineKeyboardButton('Link', url = short)
            ],
            [
                InlineKeyboardButton('Try Again ↻', url = f'https://telegram.me/{app.username}?start={b64}') ,
            ]
        ]
        if HOW_TO_DOWNLOAD:
            reply_markup[0].append(InlineKeyboardButton('Tutorial', url = HOW_TO_DOWNLOAD))
        await replyMessage(message , f'''<b>Hey {message.from_user.mention} , Your Ads Pass Is Expired , Please Go Through The Link Again !

After Passing Link You Don't Need To Pass Ad Again For Next {await get_readable_time(TOKEN_TIMEOUT)} !</b>''' , reply_markup = InlineKeyboardMarkup(
            reply_markup ))
        await sync()
        return True
    return False

async def settle_token(app , message , token_):
    user_id = str(message.from_user.id)
    if 'TOKEN' not in cf: cf['TOKEN'] = {}
    if user_id not in cf['TOKEN']: cf['TOKEN'][user_id] = {}
    token = cf['TOKEN'][user_id].get('TOKEN')
    if (not token) or token != token_:
        return await replyMessage(message , '<b>Not Your Token Or Token Invalid !</b>')
    cf['TOKEN'][user_id]['TIME'] = int(time.time()) + TOKEN_TIMEOUT
    await replyMessage( message , f'''<b>Link ByPassed Successfully For Next {await get_readable_time(TOKEN_TIMEOUT)}!
    
Now Press The Try Again Button Above Or Click Link Again From The Channel</b>''')
    del cf['TOKEN'][user_id]['TOKEN']
    await sync()

@Client.on_message(filters.command(['start']))
async def start(app , message):
    await add_user(message.from_user.id)
    stat , returned = await check_fsubs(app , message.from_user.id)
    if stat:
        text = f'''<b>Hello {message.from_user.mention}

You need to join in my Channel(s) to use me

Kindly Please join below channel(s).</b>'''
        try: returned.append(
            [InlineKeyboardButton('Try Again' , url = f"https://t.me/{app.username}?start={message.command[1]}")]
        )
        except: pass
        return await replyMessage(message , text , reply_markup = InlineKeyboardMarkup(returned))
    text = message.text
    if TOKEN_TIMEOUT:
        if len(text.split(maxsplit=1)) > 1 and text.split(maxsplit=1)[1].startswith('token'):
            await settle_token(app , message , text.split(maxsplit=1)[1].replace('token',''))
            return
    if len(text.split()) == 1:
        text = f'''<b>Hello {message.from_user.mention}
        
I can store private files in Specified Channel and other users can access it from special link.
Do /help To Know More ❤️</b>'''
        return await replyMessage(message , text , reply_markup=None)
    temp = await replyMessage(message , f'<b>Please Wait ...</b>' , reply_markup = None)
    try: base64_string = text.split()[1]
    except: return
    if TOKEN_TIMEOUT:
        if not (SHORTENER_PREMIUM and prem_dict['PREMIUM'].get(str(message.from_user.id))):
            status = await handle_token(app , message , base64_string)
            if status: 
                return await temp.delete()
    if base64_string.startswith('batch') or base64_string.startswith('download'):
        ids = await get_db_format(base64_string)
    else:
        try: string = await decode(base64_string)
        except: return
        argument = string.split('-')
        if argument[0] == 'get':
            ids = await get_old_format(argument)
        else:
            if len(argument) == 1: ids = [int(string)]
            else: ids = range(int(argument[0]) , int(argument[1]) + 1)
    if not ids: return
    try:
        messages = await asyncio.gather(*[app.get_messages(CHANNEL_ID , x) for x in ids])
        messages = [mg for mg in messages if not mg.empty]
    except:
        await replyMessage(message , "<b>Something went wrong..!</b>")
        return
    to_delete = []
    for msg in messages:
        if not (msg.video or msg.document): f_msg = await copyMessage(msg , message.chat.id , protect = PROTECT)
        else:
            filename = (msg.document or msg.video).file_name
            filesize = (msg.document or msg.video).file_size
            previouscaption = msg.caption
            f_msg = await copyMessage(msg , message.chat.id , caption = CUSTOM_CAPTION.format(
                filename = filename ,
                filesize = filesize ,
                previouscaption = previouscaption
            ) , protect = PROTECT)
        to_delete.append(f_msg)
    if AUTO_DELETE:
        to_delete.append(message)
        async def clean_messages(AUTO_DELETE , _list):
            await asyncio.sleep(AUTO_DELETE)
            asyncio.gather(*[deleteMessage(msg) for msg in _list])
        delete_msg = await replyMessage(message , f'<b>These Message Would Be Deleted In {await get_readable_time(AUTO_DELETE)} , So Save Them Somewhere Else !</b>')
        to_delete.append(delete_msg)
        loop = asyncio.get_event_loop()
        loop.create_task(clean_messages(AUTO_DELETE , to_delete))
    await temp.delete()

@Client.on_message(filters.private & filters.command('broadcast') & filters.user(OWNER))
async def send_text(client, message):
    if message.reply_to_message:
        query = users_list
        broadcast_msg = message.reply_to_message
        total = 0
        successful = 0
        blocked = 0
        deleted = 0
        unsuccessful = 0
        stats_text = """<b><u>Broadcast Processing</u>

Total Users: <code>{}</code>
Successful: <code>{}</code>
Blocked Users: <code>{}</code>
Deleted Accounts: <code>{}</code>
Unsuccessful: <code>{}</code></b>"""
        pls_wait = await replyMessage(message , "<i>Broadcasting Message.. This will Take Some Time</i>")
        for chat_id in query:
            try:
                await broadcast_msg.copy(chat_id)
                successful += 1
            except FloodWait as e:
                await asyncio.sleep(e.value * 1.5)
                await broadcast_msg.copy(chat_id)
                successful += 1
            except UserIsBlocked:
                await del_user(chat_id)
                blocked += 1
            except InputUserDeactivated:
                await del_user(chat_id)
                deleted += 1
            except:
                unsuccessful += 1
                pass
            total += 1
            if total % 5 == 0: 
                try: await pls_wait.edit( stats_text.format(total , successful , blocked , deleted , unsuccessful) )
                except: pass
        await pls_wait.delete()
        await replyMessage(message , stats_text.replace('Processing' , 'Completed').format(total , successful , blocked , deleted , unsuccessful))
    else:
        msg = await message.reply(f"`Reply To A Message !`")

@Client.on_message(filters.command('stats') & is_auth)
async def stats(bot, message):
    now = datetime.now()
    delta = now - bot.uptime
    time = await get_readable_time(delta.seconds)
    await replyMessage(message , f"<b>BOT UPTIME\n{time}</b>")

@Client.on_message(filters.command('users') & is_auth)
async def users(bot, message):
    await replyMessage(message , f"<b>Total {len(users_list)} users are using this bot !</b>")

@Client.on_message(filters.command('log') & is_auth)
async def log(bot, message):
    await message.reply_document('log.txt' , caption='<b>Log File</b>' , quote=True)

@Client.on_message(filters.command('ban') & is_auth)
async def ban_(bot , message):
    try:
        user_id = int(message.text.split(maxsplit=1)[1])
        if 'BAN' not in cf: cf['BAN'] = []
        if user_id not in cf['BAN']: 
            cf['BAN'].append(user_id)
            await message.reply_text(f'**Banned {user_id}**' , True)
            return await sync()
        await message.reply_text(f'**Already Banned {user_id}**' , True)
        await sync()
    except:
        return await message.reply_text('**Send Correct User ID**' , True)

@Client.on_message(filters.command('unban') & is_auth)
async def unban_(bot , message):
    try:
        user_id = int(message.text.split(maxsplit=1)[1])
        if 'BAN' not in cf: cf['BAN'] = []
        if user_id in cf['BAN']: 
            cf['BAN'].remove(user_id)
            await message.reply_text(f'**UnBanned {user_id}**' , True)
            return await sync()
        await message.reply_text(f'**Not Banned {user_id}**' , True)
        await sync()
    except:
        return await message.reply_text('**Send Correct User ID**' , True)

@Client.on_message(filters.command('banlist') & is_auth)
async def banlist_(bot , message):
    text = message.text.split(maxsplit=1)
    if len(text) > 1:
        user_id = text[1]
        return await message.reply_text(f"**{user_id} Ban Status : {'Banned' if user_id in cf.get('BAN' , []) else 'Not Banned'}**" , True)
    await message.reply_text(f"**Total Banned Users : {len(f['BANNED'])}**" , True)
