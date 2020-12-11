import telegram
import json
import requests
import schedule, time, datetime
import numpy as np
import pandas as pd

from functools import reduce
from database.mongobase import mongodb_database
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize 

with open('tokens.json') as f:
    token_file = json.loads(f.read())

token = token_file['telegram_token']

mongobase = mongodb_database()

def telegram_bot_sendtext(chat_id, bot_message):
    bot = telegram.Bot(token=token)
    bot.sendMessage(chat_id=chat_id, text=bot_message)

def transform_map(user_map):
    # Check values for given quadrant
    quadrant_values = zip(user_map['valence'], user_map['activation'])
    qv = list(quadrant_values)
    quadrant = []
    for v in qv:
        if v[0] > 0 and v[1] > 0:
            quadrant.append('quadrant_one')
        elif v[0] < 0 and v[1] > 0:
            quadrant.append('quadrant_two')
        elif v[0] < 0 and v[1] < 0:
            quadrant.append('quadrant_three')
        else:
            quadrant.append('quadrant_four')
    user_map.pop('activation')
    user_map.pop('valence')
    user_map['quadrant'] = quadrant

    return pd.DataFrame(user_map)

def create_quadrant_time_pairs():
    for user in mongobase.all_users():
        data = {'quadrant': None, 'time': None}
        max_morning = max_afternoon = max_evening = pd.DataFrame([data])
        user_map = user['emotion_map']
        um = transform_map(user_map)
        # Time-quadrant pairs
        pairs = um.groupby(['quadrant', 'time']).size()
        pairs = pairs.to_frame(name = 'size').reset_index()

        if 'morning' in list(pairs['time']):
            mornings = pairs.loc[pairs['time'] == 'morning'] 
            max_morning = mornings.loc[mornings['size'] == mornings['size'].max()].reset_index(drop = True)
            if len(max_morning) > 1:
                max_morning = pd.DataFrame([{'quadrant': None, 'time': None}])
        if 'afternoon' in list(pairs['time']):
            afternoons = pairs.loc[pairs['time'] == 'afternoon'] 
            max_afternoon = afternoons.loc[afternoons['size'] == afternoons['size'].max()].reset_index(drop = True)
            if len(max_afternoon) > 1:
                max_afternoon = pd.DataFrame([{'quadrant': None, 'time': None}])
        if 'evening' in list(pairs['time']):
            evenings = pairs.loc[pairs['time'] == 'evening']
            max_evening = evenings.loc[evenings['size'] == evenings['size'].max()].reset_index(drop = True)
            if len(max_evening) > 1:
                max_evening = pd.DataFrame([{'quadrant': None, 'time': None}])

        times_dict = {'morning': max_morning['quadrant'].to_string(index = False).lstrip(),
            'afternoon': max_afternoon['quadrant'].to_string(index = False).lstrip(),
            'evening': max_evening['quadrant'].to_string(index = False).lstrip()}
        
        mongobase.save_quadrant_time(user['chat_id'], times_dict, 'save')

def convert_to_hours(time_day):
    if time_day == 'morning':
        hour = np.random.randint(9, 12)
    elif time_day == 'afternoon':
        hour = np.random.randint(12, 20)
    else:
        hour = np.random.randint(20, 22)
    minutes = np.random.randint(0, 59)

    min_str = f'0{minutes}' if len(str(minutes)) == 1 else str(minutes)
    h_str = f'0{hour}' if len(str(hour)) == 1 else str(hour)

    sh = f'{h_str}:{min_str}'
    return sh

def get_times():
    times_dict = {}
    for user in mongobase.all_users():
        if user['reminders'] == 'daily':
            qt = mongobase.save_quadrant_time(user['chat_id'])
            possible_times = []
            for k, v in qt.items():
                if v != 'None' and v == 'quadrant_two' or v == 'quadrant_three':
                    nk = convert_to_hours(k)
                    possible_times.append([nk, k, v])
            if len(possible_times) == 1:
                times_dict[user['chat_id']] = possible_times[0][0]
                mongobase.save_reminder(user['chat_id'], k, v, 'save')
            elif len(possible_times) > 1:
                ind = np.random.randint(len(possible_times))
                mongobase.save_reminder(user['chat_id'], possible_times[ind][1], possible_times[ind][2], 'save')
                times_dict[user['chat_id']] = possible_times[ind][0]
    return times_dict

def create_schedule(message):
    print('New schedules')
    # Clean the previous schedule
    schedule.clear('daily')
    # Get the new hours and schedule one message per day
    schedule_dict = get_times()
    print(schedule_dict)
    for k,v in schedule_dict.items():
        schedule.every().day.at(v).do(telegram_bot_sendtext, k, message).tag('daily')

def check_hobbies():
    for user in mongobase.all_users():
        for i, sentence in enumerate(user['emotion_map']['activity']):
            hobby = compare_hobbies(sentence)
            mongobase.update_hobby(user['chat_id'], hobby, i)

def compare_hobbies(sentence):
    # Clean and tokenize the sentece
    stop_words = set(stopwords.words('english')) 
    word_tokens = word_tokenize(sentence)
    filtered_sentence = [w for w in word_tokens if not w in stop_words]

    possible_hobby = {}
    # Get the hobbies
    hobbies = mongobase.get_hobbies_list()

    for hobby in hobbies:
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
                    time.sleep(30)
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
        v = sentence

    return v

if __name__ == '__main__':
    message = 'Remember to take a break!'
    
    schedule.every().day.at('01:00').do(create_quadrant_time_pairs).tag('daily')
    schedule.every().day.at('01:00').do(check_hobbies).tag('daily')
           
    schedule.every().day.at('04:30').do(create_schedule, message)

    while True:
        schedule.run_pending()
        time.sleep(3600)
    