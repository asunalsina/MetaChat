import pymongo
import numpy as np
import json

from datetime import datetime

with open('tokens.json') as f:
    token_file = json.loads(f.read())

# Create the client and the database
client = pymongo.MongoClient(token_file['mongodb_token'])
db=client.users_database

def insert_data(informartion, chat_id, multiple, db = db):
    # User information has to be a dictionary
    user = db.users.find_one({'chat_id': chat_id})

    if user is None and not multiple:
        # Create document
        user_data = {'chat_id': chat_id}
    
        user_data.update(informartion)

        db.users.insert_one(user_data)

    elif user is None and multiple:
        user_data = {'chat_id': chat_id}
    
        db.users.insert_one(user_data)

        db.users.update_one({'chat_id': chat_id}, {'$push': informartion})

    else:
        # Update the retrieved user information
        if not multiple:
            db.users.update_one({'chat_id': chat_id}, {'$set': informartion})

        else:
            db.users.update_one({'chat_id': chat_id}, {'$push': informartion})


def get_data(field, chat_id, db = db):
    user = db.users.find_one({'chat_id' : chat_id})

    if user is not None:
        
        return user.get(field)

    else:

        print('That user does not exist')


def increment_field(field, chat_id, db = db):

    db.users.update_one({'chat_id': chat_id}, {'$inc': {field: 1}})


def hobbies_df(chat_id, db = db):
    user = db.users.find_one({'chat_id': chat_id})
    if 'hobbies' in user.keys():
        hobbies = True
    else:
        hobbies = False
    return hobbies

def save_hobbies(turn, chat_id, db = db):
    hobbies_string = turn.split(', ')
    db.users.update_one({'chat_id': chat_id}, {'$push': {'hobbies': {'$each': hobbies_string}}})

def get_hobby(chat_id, all_hobbies = False, db = db):
    user = db.users.find_one({'chat_id': chat_id})
    hobbies = user['hobbies']
    
    if all_hobbies:
        if 'hobbies' in user.keys():
            return hobbies
        else:
            return []
    else:
        return hobbies[np.random.randint(len(hobbies))]

def delete_data(chat_id, field, db = db):
    if field == 'user':
        db.users.delete_one({'chat_id': chat_id})
    elif field == 'hobbies':
        db.users.update_one({'chat_id': chat_id}, {'$unset': {'hobbies': 1}})

def set_reminder(chat_id, value = 'daily', db = db):
    db.users.update_one({'chat_id': chat_id}, {'$set': {'reminders': value}})


def metaquestion(chat_id, action = 'increment', db = db):
    if action == 'keys':
        metaquestion = 'metaquestion' in db.users.find_one({'chat_id': chat_id}).keys()
        return metaquestion
    else:  
        db.users.update_one({'chat_id': chat_id}, {'$inc': {'metaquestion': 1}})

def user_map(chat_id, text, column, db = db):

    if column == 'emotion':
        information_dict = {'map.emotion': text, 'map.time': datetime.now().strftime("%H:%M:%s"), 'map.date': datetime.now().strftime("%Y/%m/%d")}

        db.users.update_one({'chat_id': chat_id}, {'$push': information_dict})

    elif column == 'reason':
        db.users.update_one({'chat_id': chat_id}, {'$push': {'map.reason': text}})
