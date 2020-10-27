import json
import pymongo
import pandas as pd

# Load tokens
with open('tokens.json') as f:
    token_file = json.loads(f.read())

client = pymongo.MongoClient(token_file['mongodb_token'])
db=client.users_database
 
def count_pairs(user_map):

    map_df = pd.DataFrame(user_map)
    map_pairs = map_df.groupby(['emotion', 'reason']).size()
    map_pairs_df = map_pairs.to_frame(name = 'size').reset_index()

    return map_pairs_df


if __name__ == '__main__':
    
    users = db.users.find()

    for user in users:
        map_pairs = count_pairs(user['map'])

        map_pairs = map_pairs.to_dict(orient = 'list')

        db.users.update_one({'chat_id': user['chat_id']}, {'$set': {'emotion-reason':map_pairs}})
         
