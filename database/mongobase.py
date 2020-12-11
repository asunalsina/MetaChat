import pymongo
import numpy as np
import json, random, calendar

from datetime import datetime, date

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
            user_data = {'chat_id': chat_id, 'phase': 1, 'reminders': 'daily', 'last_reminder': ''}
            user_data.update(informartion)
            self.db.users.insert_one(user_data)
        elif user is None and multiple:
            user_data = {'chat_id': chat_id, 'phase': 1, 'reminders': 'daily', 'last_reminder': ''}
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
    
    def all_users(self):
        return self.db.users.find()

    def delete_data(self, chat_id):
        self.db.users.delete_one({'chat_id': chat_id})

    def set_reminder(self, chat_id, value):
        self.db.users.update_one({'chat_id': chat_id}, {'$set': {'reminders': value}})

    def emotion_map(self, chat_id, value, column):
        if column == 'valence':
            time_now = datetime.now().strftime("%H:%M")
            if time_now >= '04:00' and time_now < '12:00':
                time_day = 'morning'
            elif time_now >= '12:00' and time_now < '20:00':
                time_day = 'afternoon'
            else:
                time_day = 'evening'
            information_dict = {'emotion_map.valence': value, 'emotion_map.time': time_day, 'emotion_map.day': str(date.today()), 'emotion_map.date': calendar.day_name[datetime.today().weekday()]}
            self.db.users.update_one({'chat_id': chat_id}, {'$push': information_dict})
        elif column == 'activation':
            self.db.users.update_one({'chat_id': chat_id}, {'$push': {'emotion_map.activation': value}})
        elif column == 'activity':
            self.db.users.update_one({'chat_id': chat_id}, {'$push': {'emotion_map.activity': value}})

    def phase(self, chat_id, action = 'get'):
        if action == 'get':
            user = self.db.users.find_one({'chat_id': chat_id})
            return user['phase']
        elif action == 'change':
            self.db.users.update_one({'chat_id': chat_id}, {'$set': {'phase': new_phase}})

    def get_hobbies_list(self, number_hobbies = 'all'):
        hobbies = []
        for coll in self.db_hobbies.list_collection_names():
            doc = self.db_hobbies[coll].find_one()
            if len(doc.keys()) == 2:
                hobbies.extend(list(map(str.lower, doc['hobbies'])))
            else:
                hobbies.extend(list(map(str.lower, doc['indoor'])) + list(map(str.lower, doc['outdoor'])))
        if number_hobbies != 'all':
            hobbies = random.sample(hobbies, number_hobbies)
        return hobbies

    def get_last_message(self, chat_id, action = ''):
        user = self.db.users.find_one({'chat_id': chat_id})
        last_utterance = user['conversation'][-2]
        last_utterance = last_utterance.split(' - ')
        if action == 'save':
            self.db.users.update_one({'chat_id': chat_id}, {'$set': {'last_utterance': last_utterance[4]}})
        return last_utterance[4]

    def get_selected_conversation(self, chat_id, action):
        user = self.db.users.find_one({'chat_id': chat_id})
        if action == 'get':
            if 'active_conversation' in user.keys():
                la = user['active_conversation']
                if la < 3:
                    return la
                else:
                    new_la = np.random.randint(3)
                    self.db.users.update_one({'chat_id': chat_id}, {'$set': {'active_conversation': new_la}})
                    return new_la
            else:
                self.db.users.update_one({'chat_id': chat_id}, {'$set': {'active_conversation': 3}})

        elif action == 'set':
            self.db.users.update_one({'chat_id': chat_id}, {'$set': {'active_conversation': 3}})


    def get_user_map(self, chat_id):
        user = self.db.users.find_one({'chat_id': chat_id})
        return user['emotion_map']

    def get_last_field(self, chat_id, field, value = '', action = 'get'):
        if action == 'get':
            user = self.db.users.find_one({'chat_id': chat_id})
            return user[f'last_{field}']
        elif action == 'save':
            self.db.users.update_one({'chat_id': chat_id}, {'$set': {f'last_{field}': value}})

    def save_quadrant_time(self, chat_id, value = '', action = 'get'):
        if action == 'save':
            self.db.users.update_one({'chat_id': chat_id}, {'$set': {'quadrant_time': value}})
        else:
            user = self.db.users.find_one({'chat_id': chat_id})
            return user['quadrant_time']

    def update_hobby(self, chat_id, hobby, index):
        self.db.users.update_one({'chat_id': chat_id}, {'$set': {f'emotion_map.activity.{index}': hobby}})

    def save_reminder(self, chat_id, time = '', quadrant = '', action = 'get'):
        if action == 'get':
            user = self.db.users.find_one({'chat_id': chat_id})
            return user['last_reminder']
        else:
            data = {'time': time, 'quadrant': quadrant}
            self.db.users.update_one({'chat_id': chat_id}, {'$set': {'last_reminder': data}})

