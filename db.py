from pymongo import MongoClient
from var import *

client=MongoClient(DB_URL)
db=client[DB_NAME]
col=db['users']

users_list = []
full = col.find()
for doc in full:
        users_list.append(doc['_id'])

async def add_user(ids):
        if ids not in users_list:
                try: col.insert_one({'_id' : ids})
                except: pass
                users_list.append(ids)

async def del_user(ids):
        if ids in users_list:
                try: col.delete_one({'_id':ids})
                except: pass
                users_list.remove(ids)

# TOKEN SYSTEM
tcol = db['token']

cf = tcol.find_one({'_id':'token'})
if not cf:
        cf = {'_id':'token'}
        tcol.insert_one(cf)

async def sync():
        tcol.replace_one({'_id':'token'},cf)

# PREMIUM_USERS

prem = db['premium']

prem_dict = prem.find_one({'_id':'premium'})
if not prem_dict:
        prem_dict = {'_id':'premium'}
        prem.insert_one(prem_dict)

if 'PREMIUM' not in prem_dict: prem_dict['PREMIUM'] = {}

for key , value in prem_dict['PREMIUM'].items():
        value.update({'END' : value['END'].astimezone(TIME_ZONE)})

async def prem_sync():
        prem.replace_one({'_id':'premium'},prem_dict)


old_data = {}

for i in db['files'].find({}):
        old_data[i['_id']] = i