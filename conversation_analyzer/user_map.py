import json, pymongo, requests
import pandas as pd

from tqdm import tqdm

import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize 

# Load tokens
with open('tokens.json') as f:
    token_file = json.loads(f.read())

client = pymongo.MongoClient(token_file['mongodb_token'])
db = client.users_database
db_hobbies = client.hobbies
 
def count_pairs(user_map):
    map_df = pd.DataFrame(user_map)
    map_pairs = map_df.groupby(['emotion', 'reason']).size()
    map_pairs_df = map_pairs.to_frame(name = 'size').reset_index()

    return map_pairs_df

def count_activities(user_map):
    map_df = pd.DataFrame(user_map)
    map_pairs = map_df.groupby(['emotion', 'reason', 'activity']).size()
    map_pairs_df = map_pairs.to_frame(name = 'size').reset_index()

    return map_pairs_df

def get_hobby_relatedness(sentence, db_hobbies = db_hobbies):
    # Clean and tokenize the sentece
    stop_words = set(stopwords.words('english')) 
    word_tokens = word_tokenize(sentence)
    filtered_sentence = [w for w in word_tokens if not w in stop_words]

    # Get the hobbies
    hobbies = []
    possible_hobby = {}
    for coll in db_hobbies.list_collection_names():
        doc = db_hobbies[coll].find_one()

        if len(doc.keys()) == 2:
            hobbies.extend(list(map(str.lower, doc['hobbies'])))
        
        else:
            hobbies.extend(list(map(str.lower, doc['indoor'])) + list(map(str.lower, doc['outdoor'])))

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

if __name__ == '__main__':
    
    users = db.users.find()

    for user in users:
        if 'map' in user.keys():
            map_pairs = count_pairs(user['map'])
            map_pairs = map_pairs.to_dict(orient = 'list')
            db.users.update_one({'chat_id': user['chat_id']}, {'$set': {'emotion-reason':map_pairs}})

            map_df = pd.DataFrame(user['map'])
            activities = [get_hobby_relatedness(a) if a.lower() != 'nothing' else a.lower() for a in map_df['activity']]
            db.users.update_one({'chat_id': user['chat_id']}, {'$set': {'map.activity': activities}})

            if 'activity' in user['map'].keys():
                activity_map = count_activities(user['map'])
                activity_map = activity_map.to_dict(orient = 'list')
                db.users.update_one({'chat_id': user['chat_id']}, {'$set': {'emotion-reason-activity':activity_map}})
         
