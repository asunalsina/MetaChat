import json, requests
import pandas as pd

from tqdm import tqdm

import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize 

from database.mongobase import mongodb_database

mongobase = mongodb_database()
 
def count_pairs(user_map):
    map_df = pd.DataFrame(user_map)
    map_pairs = map_df.groupby(['emotion', 'reason']).size()
    map_pairs_df = map_pairs.to_frame(name = 'size').reset_index()
    map_pairs = map_pairs_df.to_dict(orient = 'list')
    return map_pairs

def count_activities(user_map):
    map_df = pd.DataFrame(user_map)
    map_pairs = map_df.groupby(['emotion', 'reason', 'activity']).size()
    map_pairs_df = map_pairs.to_frame(name = 'size').reset_index()
    activity_map = map_pairs_df.to_dict(orient = 'list')
    return activity_map

def get_hobby_relatedness(sentence):
    # Clean and tokenize the sentece
    stop_words = set(stopwords.words('english')) 
    word_tokens = word_tokenize(sentence)
    filtered_sentence = [w for w in word_tokens if not w in stop_words]

    possible_hobby = {}
    # Get the hobbies
    hobbies = mongobase.get_hobbies_list()

    for hobby in tqdm(hobbies):
        hobby_split = hobby.split(' ')
        if len(hobby_split) > 1:
            hobby = '_'.join(hobby_split)

        for word in filtered_sentence:
            test_var = True
            relatedness = f'http://api.conceptnet.io/relatedness?node1=/c/en/{word}&node2=/c/en/{hobby}'
            while test_var:
                try:
                    obj = requests.get(relatedness).json()
                    test_var = False
                except:
                    continue

            if obj['value'] >= 0.5:
                if len(possible_hobby.keys()) == 0:
                    possible_hobby[obj['value']] = hobby
                else:
                    [(k,v)] = possible_hobby.items()
                    if obj['value'] > k:
                        possible_hobby.pop(k)
                        possible_hobby[obj['value']] = hobby

    if len(possible_hobby.keys()) > 0:
        [(k, v)] = possible_hobby.items()
    else:
        v = 'nothing'

    return v

def change_phase(chat_id, mode='manual'):
    if mode == 'auto':
        total_calls = mongobase.conversation_calls(chat_id)
        if total_calls > 50 and total_calls < 100:
            new_phase = 2
            mongobase.change_phase(chat_id, new_phase)
        elif total_calls >= 100:
            new_phase = 3
            mongobase.change_phase(chat_id, new_phase)

if __name__ == '__main__':
    
    users = mongobase.all_users()

    for user in users:
        # Change the phase of the users automatically
        change_phase(user['chat_id'])
        # Calculate the new emotion-reason and emotion-reason-activity tables
        if 'map' in user.keys():
            map_pairs = count_pairs(user['map'])
            mongobase.update_emotion_table(user['chat_id'], map_pairs, 'reason')
            # Update the user activities checking the relatedness with the activities in the database
            map_df = pd.DataFrame(user['map'])
            activities = [get_hobby_relatedness(a) if a.lower() != 'nothing' else a.lower() for a in map_df['activity']]
            mongobase.user_map(user['chat_id'], activities, 'change_activities')

            if 'activity' in user['map'].keys():
                activity_map = count_activities(user['map'])
                mongobase.update_emotion_table(user['chat_id'], activity_map, 'activity')
                
         
