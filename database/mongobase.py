import pymongo
import numpy as np
import json

from datetime import datetime

with open('tokens.json') as f:
    token_file = json.loads(f.read())


class mongodb_database(object):
    def __init__(self):
        self.client = pymongo.MongoClient(token_file['mongodb_token'])
        self.db = self.client.users_database
        self.db_hobbies = self.client.hobbies
        
    def insert_data(self, informartion, chat_id, multiple):
        # User information has to be a dictionary
        user = self.db.users.find_one({'chat_id': chat_id})
        if user is None and not multiple:
            # Create document
            user_data = {'chat_id': chat_id, 'phase': 1}
            user_data.update(informartion)
            self.db.users.insert_one(user_data)
        elif user is None and multiple:
            user_data = {'chat_id': chat_id, 'phase': 1}
            self.db.users.insert_one(user_data)
            self.db.users.update_one({'chat_id': chat_id}, {'$push': informartion})
        else:
            # Update the retrieved user information
            if not multiple:
                self.db.users.update_one({'chat_id': chat_id}, {'$set': informartion})
            else:
                self.db.users.update_one({'chat_id': chat_id}, {'$push': informartion})

    def get_data(self, field, chat_id):
        user = self.db.users.find_one({'chat_id' : chat_id})
        if user is not None:
            return user.get(field)
        else:
            print('That user does not exist')

    def increment_field(self, field, chat_id):
        self.db.users.update_one({'chat_id': chat_id}, {'$inc': {field: 1}})

    def delete_data(self, chat_id):
        self.db.users.delete_one({'chat_id': chat_id})

    def set_reminder(self, chat_id, value = 'daily'):
        self.db.users.update_one({'chat_id': chat_id}, {'$set': {'reminders': value}})

    def metaquestion(self, chat_id, action = 'increment'):
        if action == 'keys':
            metaquestion = 'metaquestion' in self.db.users.find_one({'chat_id': chat_id}).keys()
            return metaquestion
        else:  
            db.users.update_one({'chat_id': chat_id}, {'$inc': {'metaquestion': 1}})

    def user_map(self, chat_id, text, column):
        if column == 'emotion':
            information_dict = {'map.emotion': text, 'map.time': datetime.now().strftime("%H:%M:%s"), 'map.date': datetime.now().strftime("%Y/%m/%d")}
            self.db.users.update_one({'chat_id': chat_id}, {'$push': information_dict})
        elif column == 'reason':
            self.db.users.update_one({'chat_id': chat_id}, {'$push': {'map.reason': text}})
        elif column == 'activity':
            self.db.users.update_one({'chat_id': chat_id}, {'$push': {'map.activity': text}})
        elif column == 'change_activities':
            self.db.users.update_one({'chat_id': chat_id}, {'$set': {'map.activity': text}})

    def get_map_pairs(self, chat_id, value):
        user = self.db.users.find_one({'chat_id': chat_id})
        if value == 'reason':
            return user['emotion-reason']
        elif value == 'activity':
            return user['emotion-reason-activity']

    def get_phase(self, chat_id):
        user = self.db.users.find_one({'chat_id': chat_id})
        return user['phase']

    def change_phase(self, chat_id, new_phase):
        self.db.users.update_one({'chat_id': chat_id}, {'$set': {'phase': new_phase}})

    def get_hobbies_list(self):
        hobbies = []
        for coll in self.db_hobbies.list_collection_names():
            doc = self.db_hobbies[coll].find_one()
            if len(doc.keys()) == 2:
                hobbies.extend(list(map(str.lower, doc['hobbies'])))
            else:
                hobbies.extend(list(map(str.lower, doc['indoor'])) + list(map(str.lower, doc['outdoor'])))
        return hobbies

    def update_emotion_table(self, chat_id, map_pairs, table):
        if table == 'reason':
            self.db.users.update_one({'chat_id': chat_id}, {'$set': {'emotion-reason':map_pairs}})
        elif table == 'activity':
            self.db.users.update_one({'chat_id': chat_id}, {'$set': {'emotion-reason-activity':map_pairs}})

    def all_users(self):
        return self.db.users.find()

    def conversation_calls(self, chat_id):
        user = self.db.users.find_one({'chat_id': chat_id})
        total_calls = user['feelings'] + user['current_situation']
        return total_calls

    def last_emotion(self, chat_id, action, le = []):
        if action == 'get':
            user = self.db.users.find_one({'chat_id': chat_id})
            if 'last_emotion' in user.keys():
                return user['last_emotion']
            else:
                return []
        elif action == 'save':
            self.db.users.update_one({'chat_id': chat_id}, {'$set': {'last_emotion': le}})

    def last_activity(self, chat_id, action, la = []):
        if action == 'get':
            user = self.db.users.find_one({'chat_id': chat_id})
            if 'last_activity' in user.keys():
                return user['last_activity']
            else:
                return []
        elif action == 'save':
            self.db.users.update_one({'chat_id': chat_id}, {'$set': {'last_activity': la}})

