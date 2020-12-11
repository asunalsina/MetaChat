import numpy as np
import string, json, random
import calendar, math

from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import pandas as pd

from database.mongobase import mongodb_database

from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize 

from telegram import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove

with open('rulebased/rule_sentences.json') as file:
    sentences = json.loads(file.read())

mongobase = mongodb_database()

### PHASE 1 ###
def feelings_phase_one(stage, meta_conversation, user_message, chat_id, sentences = sentences):
    keywords = ['sleep', 'die', 'kill', 'nothing', 'suicide']

    if stage == 0:
        bot_message = sentences['feelings'][stage]
        button_list = sentences['buttons']['yes_no']
        rm = ReplyKeyboardMarkup(button_list)

    elif stage == 1:
        if user_message.lower() == 'yes':
            bot_message = sentences['feelings'][stage][0]
            button_list = sentences['buttons']['valence']
            rm = ReplyKeyboardMarkup(button_list)
        else:
            bot_message = sentences['feelings'][stage][1]
            rm = ReplyKeyboardRemove()
            meta_conversation = False

    elif stage == 2:
        # Save valence value
        value = transform_value(user_message.lower(), 'valence')
        mongobase.emotion_map(chat_id, value, 'valence')

        bot_message = sentences['feelings'][stage]
        button_list = sentences['buttons']['activation']
        rm = ReplyKeyboardMarkup(button_list)

    elif stage == 3:
        # Save activation value
        value = transform_value(user_message.lower(), 'activation')
        mongobase.emotion_map(chat_id, value, 'activation')

        bot_message = sentences['feelings'][stage]
        rm = ReplyKeyboardRemove()

    elif stage == 4:
        if any(True for word in user_message.lower().split() if word in keywords):
            # Get activities from database
            common_activities = mongobase.get_hobbies_list(3)
            bot_message = sentences['feelings'][stage][0]
            button_list = [[a.capitalize()] for a in common_activities]
            rm = ReplyKeyboardMarkup(button_list)
        else: 
            # Save activity
            mongobase.emotion_map(chat_id, user_message.lower(), 'activity')
            bot_message = sentences['feelings'][stage][1]
            rm = ReplyKeyboardRemove()
            meta_conversation = False

    elif stage == 5:
        # Save activity
        mongobase.emotion_map(chat_id, user_message.lower(), 'activity')
        bot_message = sentences['feelings'][stage]
        rm = ReplyKeyboardRemove()
        meta_conversation = False

    return rm, bot_message, meta_conversation

def workings_conversation(stage, meta_conversation, user_message, chat_id, entity, phase, sentences = sentences):
    if 'meta' == entity.get('name'):
        if phase == 1:
            rm, bot_message, meta_conversation = user_conversation(stage, meta_conversation, user_message, chat_id, sentences = sentences)
        elif phase == 2:
            rm, bot_message, meta_conversation = user_phase_two(stage, meta_conversation, user_message, chat_id, sentences = sentences)
    elif 'malfunction' == entity.get('name'):
        rm, bot_message, meta_conversation = malfunction_conversation(stage, meta_conversation, user_message, chat_id, sentences = sentences)

    return rm, bot_message, meta_conversation

def malfunction_conversation(stage, meta_conversation, user_message, chat_id, sentences = sentences):
    if stage == 0:
        bot_message = sentences['malfunction'][stage] 
        button_list = sentences['buttons']['malfunction']
        rm = ReplyKeyboardMarkup(button_list)
            
    elif stage == 1:
        if user_message.lower() == 'other':
            bot_message = sentences['malfunction'][stage][1]
            rm = ReplyKeyboardRemove()

        else:
            bot_message = sentences['malfunction'][stage][0] %(user_message.lower())
            rm = ReplyKeyboardRemove()

    elif stage == 2:
            bot_message = sentences['malfunction'][stage]
            rm = {}
            meta_conversation = False

    return rm, bot_message, meta_conversation

def user_conversation(stage, meta_conversation, user_message, chat_id, sentences = sentences):
    if stage == 0:
        bot_message = sentences['user_data'][stage]
        button_list = sentences['buttons']['data']
        rm = ReplyKeyboardMarkup(button_list)

    elif stage == 1:
        # Manage my data
        if user_message.lower() == sentences['buttons']['data'][0][0].lower():
            bot_message = sentences['user_data'][stage][0]
            button_list = button_list = sentences['buttons']['yes_no']
            rm = ReplyKeyboardMarkup(button_list)
        # Know how my data is used
        elif user_message.lower() == sentences['buttons']['data'][1][0].lower():
            bot_message = sentences['user_data'][stage][1]
            rm = ReplyKeyboardRemove()
            meta_conversation = False
        # Why certain questions are asked?
        elif user_message.lower() == sentences['buttons']['data'][2][0].lower():
            bot_message = sentences['user_data'][stage][2]
            rm = ReplyKeyboardRemove()
            meta_conversation = False

    elif stage == 2:
        # Delete data
        if user_message.lower() == 'yes':
            mongobase.delete_data(chat_id)
            bot_message = sentences['profile_data'][0]
            rm = ReplyKeyboardRemove()
            meta_conversation = False

        elif user_message.lower() == 'no':
            bot_message = 'Okay!'
            rm = ReplyKeyboardRemove()
            meta_conversation = False   

    return rm, bot_message, meta_conversation

### PHASE 2 ###
# Talk about what is happening conversation
def feelings_talk(stage, meta_conversation, user_message, chat_id, entity, sentences = sentences):
    if stage == 0:
        q = 2 if entity.get('name') == 'quadrant_two' else 3
        mongobase.get_last_field(chat_id, 'quadrant', q, 'save')
        bot_message = sentences['talk_about'][stage][np.random.randint(len(sentences['talk_about'][stage]))]
        button_list = sentences['buttons']['talk']
        rm = ReplyKeyboardMarkup(button_list)
    
    elif stage == 1:
        if user_message.lower() == 'i want to talk about it':
            bot_message = sentences['talk_about'][stage][0][np.random.randint(len(sentences['talk_about'][stage]))]
            rm = ReplyKeyboardRemove()
        else:
            bot_message = sentences['talk_about'][stage][1]
            rm = ReplyKeyboardRemove()
            meta_conversation = False
    
    elif stage == 2:
        temporal_measure = check_temporal_measure(user_message.lower())
        if temporal_measure:
            bot_message = sentences['talk_about'][stage][1]
            rm = {}
            meta_conversation = False
        else:
            bot_message = sentences['talk_about'][stage][np.random.randint(len(sentences['talk_about'][stage]))]
            rm = {}

    elif stage == 3:
        bot_message = sentences['talk_about'][stage]
        rm = {}
        meta_conversation = False

    return rm, bot_message, meta_conversation

def feelings_reconnect(stage, meta_conversation, user_message, chat_id, entity, sentences = sentences):
    if stage == 0:
        q = 2 if entity.get('name') == 'quadrant_two' else 3
        mongobase.get_last_field(chat_id, 'quadrant', q, 'save')
        bot_message = sentences['reconnect_present'][stage][np.random.randint(len(sentences['reconnect_present'][stage]))]
        button_list = sentences['buttons']['yes_no']
        rm = ReplyKeyboardMarkup(button_list)

    elif stage == 1:
        if user_message.lower() == 'yes':
            lm = mongobase.get_last_message(chat_id, 'save')

            if lm == sentences['reconnect_present'][stage-1][0]:
                bot_message = sentences['reconnect_present'][stage][0]
                rm = ReplyKeyboardRemove()
                meta_conversation = False

            elif lm == sentences['reconnect_present'][stage-1][1]:
                bot_message = sentences['reconnect_present'][stage][1]
                rm = ReplyKeyboardRemove()

            elif lm == sentences['reconnect_present'][stage-1][2]:
                bot_message = sentences['reconnect_present'][stage][2]
                rm = ReplyKeyboardRemove()     
        else:
            bot_message = sentences['reconnect_present'][stage][3]
            rm = ReplyKeyboardRemove()
            meta_conversation = False

    elif stage == 2:
        bot_message = sentences['reconnect_present'][stage]
        rm = {}
        meta_conversation = False

    return rm, bot_message, meta_conversation

def feelings_suggest(stage, meta_conversation, user_message, chat_id, entity, sentences = sentences):
    keywords = ['sleep', 'die', 'kill', 'nothing', 'suicide', 'none']
    entity_name = entity.get('name')
    if stage == 0:
        if entity_name == 'quadrant_two':
            mongobase.get_last_field(chat_id, 'quadrant', 2, 'save')
            bot_message = sentences['suggest_activity'][stage][0]
        elif entity_name == 'quadrant_three':
            mongobase.get_last_field(chat_id, 'quadrant', 3, 'save')
            bot_message = sentences['suggest_activity'][stage][1]
        button_list = sentences['buttons']['yes_no']
        rm = ReplyKeyboardMarkup(button_list)

    elif stage == 1:
        if user_message.lower() == 'yes':
            hobby = user_hobby(entity_name, chat_id)
            mongobase.get_last_field(chat_id, 'activity', hobby, 'save')
            bot_message = sentences['suggest_activity'][stage][0] %(hobby[2])
            rm = ReplyKeyboardRemove()
            meta_conversation = False
        else:
            bot_message = sentences['suggest_activity'][stage][1]
            button_list = sentences['buttons']['activation']
            rm = ReplyKeyboardMarkup(button_list)
        
    elif stage == 2:
        # Save activation value
        value = transform_value(user_message.lower(), 'activation')
        mongobase.emotion_map(chat_id, value, 'activation')

        bot_message = sentences['suggest_activity'][stage]
        button_list = sentences['buttons']['valence']
        rm = ReplyKeyboardMarkup(button_list)

    elif stage == 3:
        # Save activation value
        value = transform_value(user_message.lower(), 'valence')
        mongobase.emotion_map(chat_id, value, 'valence')

        bot_message = sentences['suggest_activity'][stage]
        rm = ReplyKeyboardRemove()

    elif stage == 4:
        if any(True for word in user_message.lower().split() if word in keywords):
            # Get activities from database
            common_activities = mongobase.get_hobbies_list(3)
            bot_message = sentences['suggest_activity'][stage][0]
            button_list = [[a.capitalize()] for a in common_activities]
            rm = ReplyKeyboardMarkup(button_list)
        else: 
            # Save activity
            mongobase.emotion_map(chat_id, user_message.lower(), 'activity')
            bot_message = sentences['suggest_activity'][stage][1]
            rm = ReplyKeyboardRemove()
            meta_conversation = False

    elif stage == 5:
        # Save activity
        mongobase.emotion_map(chat_id, user_message.lower(), 'activity')
        bot_message = sentences['suggest_activity'][stage]
        rm = ReplyKeyboardRemove()
        meta_conversation = False

    return rm, bot_message, meta_conversation

def feelings_phase_two(stage, meta_conversation, user_message, chat_id, entity, sentences = sentences):
    selected_conversation = mongobase.get_selected_conversation(chat_id, 'get')

    if selected_conversation == 0:
        rm, bot_message, meta_conversation = feelings_talk(stage, meta_conversation, user_message, chat_id, entity, sentences = sentences)
        mongobase.get_last_field(chat_id, 'conversation', selected_conversation, 'save')

    elif selected_conversation == 1:
        rm, bot_message, meta_conversation = feelings_reconnect(stage, meta_conversation, user_message, chat_id, entity, sentences = sentences)
        mongobase.get_last_field(chat_id, 'conversation', selected_conversation, 'save')
    
    elif selected_conversation == 2:
        rm, bot_message, meta_conversation = feelings_suggest(stage, meta_conversation, user_message, chat_id, entity, sentences = sentences)
        mongobase.get_last_field(chat_id, 'conversation', selected_conversation, 'save')

    return rm, bot_message, meta_conversation

def user_phase_two(stage, meta_conversation, user_message, chat_id, sentences = sentences):
    if stage == 0:
        buttons = other_buttons(chat_id)
        bot_message = sentences['user_phase_2'][stage]
        button_list = sentences['buttons']['data_2']
        if buttons:
            for b in buttons:
                button_list.append(b)
        rm = ReplyKeyboardMarkup(button_list)

    elif stage == 1:
        # Manage my data
        if user_message.lower() == sentences['buttons']['data_2'][0][0].lower():
            bot_message = sentences['user_phase_2'][stage][0]
            button_list = button_list = sentences['buttons']['profile']
            rm = ReplyKeyboardMarkup(button_list)
        # Know how my data is used
        elif user_message.lower() == sentences['buttons']['data_2'][1][0].lower():
            bot_message = sentences['user_phase_2'][stage][1]
            rm = ReplyKeyboardRemove()
            meta_conversation = False
        # Why did you suggest that activity?
        elif user_message.lower() == sentences['buttons']['data_2'][2][0].lower():
            last_activity = mongobase.get_last_field(chat_id, 'activity')
            last_quadrant = mongobase.get_last_field(chat_id, 'quadrant')
            if last_activity[3] == 'last':
                energy_level = 'high' if last_quadrant == 2 else 'low'
                bot_message = sentences['why_activity'][0] %(last_activity[2], last_activity[3], last_activity[0], last_activity[1], energy_level)
            elif last_activity[3] == 'a couple' or last_activity[3] == 'a few':
                energy_level = 'high' if last_quadrant == 2 else 'low'
                bot_message = sentences['why_activity'][1] %(last_activity[2], last_activity[3], last_activity[0], last_activity[1], energy_level)
            else:
                bot_message = sentences['why_activity'][2]
            rm = ReplyKeyboardRemove()
            meta_conversation = False
        # Why did you suggest me to try that quick activity / write a short-term list / tell you three I am grateful for today
        elif any(b[0] for b in sentences['buttons']['other'][1:4] if b[0].lower() == user_message.lower()):
            present_activities = [b[0] for b in sentences['buttons']['other'][1:4] if b[0].lower() == user_message.lower()]
            suggestion = present_activities[0].replace('to', '?').split('?')
            bot_message = sentences['why_present'][0] %(suggestion[1])
            rm = ReplyKeyboardRemove()
            meta_conversation = False
        # Why did you ask me if I wanted to talk about my feelings
        elif user_message.lower() == sentences['buttons']['other'][0][0].lower():
            last_quadrant = mongobase.get_last_field(chat_id, 'quadrant')
            energy_level = 'high' if last_quadrant == 2 else 'low'
            bot_message = sentences['why_talk'][0] %(energy_level)
            rm = ReplyKeyboardRemove()
            meta_conversation = False
        # Why did you send me that reminder
        elif user_message.lower() == sentences['buttons']['other'][4][0].lower():
            lr = mongobase.save_reminder(chat_id)
            energy_level = 'high' if lr['quadrant'] == 'quadrant_two' else 'low'
            bot_message = sentences['why_reminder'][0] %(lr['time'], energy_level)
            rm = ReplyKeyboardRemove()
            meta_conversation = False

    elif stage == 2:
        # Delete data
        if user_message.lower() == sentences['buttons']['profile'][0][0].lower():
            bot_message = sentences['profile_data'][1]
            button_list = sentences['buttons']['yes_no']
            rm = ReplyKeyboardMarkup(button_list)
        # Manage reminders
        elif user_message.lower() == sentences['buttons']['profile'][1][0].lower():
            bot_message = sentences['profile_data'][2]
            button_list = sentences['buttons']['reminder']
            rm = ReplyKeyboardMarkup(button_list)

    elif stage == 3:
        # Delete data
        if user_message.lower() == 'yes':
            mongobase.delete_data(chat_id)
            bot_message = sentences['profile_data'][0]
            rm = ReplyKeyboardRemove()
            meta_conversation = False

        elif user_message.lower() == 'no':
            bot_message = 'Okay!'
            rm = ReplyKeyboardRemove()
            meta_conversation = False

        elif user_message.lower() == sentences['buttons']['reminder'][0][0].lower() or user_message.lower() == sentences['buttons']['reminder'][1][0].lower():
            mongobase.set_reminder(chat_id, user_message.lower())
            bot_message = 'Okay!'
            rm = ReplyKeyboardRemove()
            meta_conversation = False

    return rm, bot_message, meta_conversation


# Useful functions
def transform_value(text, option):
    valence_dict = {'very pleasant': 2, 'somewhat pleasant': 1, 'it is okay': 0, 
                    'somewhat unpleasant': -1, 'very unpleasant': -2}
    activation_dict = {'very energized': 2, 'somewhat energized': 1, 'neither of them': 0, 
                    'somewhat tired': -1, 'very tired': -2}
    if option == 'valence':
        value = valence_dict[text]
    elif option == 'activation':
        value = activation_dict[text]
    return value

def check_temporal_measure(text):
    # Clean and tokenize the sentece
    stop_words = set(stopwords.words('english')) 
    word_tokens = word_tokenize(text)
    filtered_text = [w for w in word_tokens if not w in stop_words]

    keywords = ['month', 'months', 'year', 'years', 'day', 'days', 'hour', 'hours', 
    'minute', 'minutes', 'seconds', 'january', 'february', 'march', 'april',
    'may', 'june', 'july', 'august', 'september', 'october', 'november', 'december',
    'yesterday', 'today']
    
    numbers = re.findall(r'\d+', text)

    if any(w for w in filtered_text if w in keywords) or numbers:
        temporal_measure = True
    else:
        temporal_measure = False

    return temporal_measure

def get_number_weeks(past_date):
    today_date = date.today()
    past_date = datetime.strptime(past_date, '%Y-%m-%d')
    past_date = past_date.date()
    days = relativedelta(today_date, past_date)

    if not days.months and not days.years:
        weeks = math.ceil((days.days%365)/7)
        if weeks == 1 or days.days == 0:
            nw = 'last'
        elif weeks == 2:
            nw = 'a couple'
        else:
            nw = 'a few'
        return nw
    else:
        return None

def other_buttons(chat_id):
    buttons = []
    selected_conversation = mongobase.get_last_field(chat_id, 'conversation')
    last_reminder = mongobase.get_last_field(chat_id, 'reminder')
    # Talk about
    if selected_conversation == 0:
        buttons = sentences['buttons']['other'][0]
    # Reconnect
    elif selected_conversation == 1:
        lm = mongobase.get_last_message(chat_id)
        if 'short-term' in lm:
            buttons = sentences['buttons']['other'][1]
        elif 'grateful' in lm:
            buttons = sentences['buttons']['other'][2]
        else:
            buttons = sentences['buttons']['other'][3] 
    if last_reminder:
        buttons.append(sentences['buttons']['other'][4])

    return buttons

def transform_user_map(user_map):
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

def selected_activity(pa, oa):
    if len(pa) == 1:
        return pa['date'].to_string(index = False).lstrip(), pa['time'].to_string(index = False).lstrip(), pa['activity'].to_string(index = False).lstrip(), pa['week'].to_string(index = False).lstrip()
    elif len(pa) > 1:
        if 'last' in pa['week'].unique():
            fs = pa.loc[pa['week'] == 'last'].reset_index(drop = True)
        elif 'a couple' in pa['week'].unique():
            fs = pa.loc[pa['week'] == 'a couple'].reset_index(drop = True)
        else:    
            fs = pa.loc[pa['week'] == 'a few'].reset_index(drop = True)
        fs = fs.iloc[np.random.randint(len(fs))]
        return fs['date'], fs['time'], fs['activity'], fs['week']
    else:
        if len(oa) == 1:
            return oa['date'].to_string(index = False).lstrip(), oa['time'].to_string(index = False).lstrip(), oa['activity'].to_string(index = False).lstrip(), oa['week'].to_string(index = False).lstrip()
        elif len(oa) > 1:
            if 'last' in oa['week'].unique():
                fs = oa.loc[oa['week'] == 'last'].reset_index(drop = True)
            elif 'a couple' in oa['week'].unique():
                fs = oa.loc[oa['week'] == 'a couple'].reset_index(drop = True)
            else:    
                fs = oa.loc[oa['week'] == 'a few'].reset_index(drop = True)
            fs = fs.iloc[np.random.randint(len(fs))]
            return fs['date'], fs['time'], fs['activity'], fs['week']

def check_quadrant(quadrant_pairs, user_map, time_day):
    # Possible activities and other activities dataframe
    pa = pd.DataFrame()
    oa = pd.DataFrame()

    if len(quadrant_pairs) == 1:
        row = user_map.loc[user_map['activity'] == quadrant_pairs['activity'].to_string(index = False).lstrip()]
        week = get_number_weeks(row['day'].to_string(index = False).lstrip())
        return row['date'].to_string(index = False).lstrip(), row['time'].to_string(index = False).lstrip(), row['activity'].to_string(index = False).lstrip(), week
    
    elif len(quadrant_pairs) > 1:
        max_activity = quadrant_pairs.loc[quadrant_pairs['size'] == quadrant_pairs['size'].max()].reset_index(drop = True)
        if len(max_activity) == 1:
            row = user_map.loc[user_map['activity'] == max_activity['activity'].to_string(index = False).lstrip()]
            for r in row.iterrows():
                if r[1]['time'] == time_day:
                    week = get_number_weeks(r[1]['day'])
                    r[1]['week'] = week
                    pa = pa.append(r[1])
                else:
                    week = get_number_weeks(r[1]['day'])
                    r[1]['week'] = week
                    oa = oa.append(r[1])
        else:
            for a in max_activity['activity']:
                row = user_map.loc[user_map['activity'] == a].copy()
                if row['time'].to_string(index = False).lstrip() == time_day:
                    week = get_number_weeks(row['day'].to_string(index = False).lstrip())
                    row['week'] = week
                    pa = pa.append(row)
                else:
                    week = get_number_weeks(row['day'].to_string(index = False).lstrip())
                    row['week'] = week
                    oa = oa.append(row)

        return selected_activity(pa, oa)

def user_hobby(entity_name, chat_id):
    user_map = mongobase.get_user_map(chat_id)
    # Check the time and classify it
    time_now = datetime.now().strftime("%H:%M")
    if time_now >= '04:00' and time_now < '12:00':
        time_day = 'morning'
    elif time_now >= '12:00' and time_now < '20:00':
        time_day = 'afternoon'
    else:
        time_day = 'evening'

    user_map = transform_user_map(user_map)

    # Activity-quadrant pairs
    pairs = user_map.groupby(['quadrant', 'activity']).size()
    pairs = pairs.to_frame(name = 'size').reset_index()
    # Pairs of the detected quadrant
    quadrant_pairs = pairs.loc[pairs['quadrant'] == entity_name]

    if len(quadrant_pairs) == 0 and entity_name == 'quadrant_two':
        quadrant_pairs = pairs.loc[pairs['quadrant'] == 'quadrant_one'] 
        if len(quadrant_pairs) == 0:
            quadrant_pairs = pairs.loc[pairs['quadrant'] == 'quadrant_four']
            if len(quadrant_pairs) == 0:
                quadrant_pairs = pairs.loc[pairs['quadrant'] == 'quadrant_three']

    elif len(quadrant_pairs) == 0 and entity_name == 'quadrant_three':
        quadrant_pairs = pairs.loc[pairs['quadrant'] == 'quadrant_four'] 
        if len(quadrant_pairs) == 0:
            quadrant_pairs = pairs.loc[pairs['quadrant'] == 'quadrant_one']
            if len(quadrant_pairs) == 0:
                quadrant_pairs = pairs.loc[pairs['quadrant'] == 'quadrant_two']

    return check_quadrant(quadrant_pairs, user_map, time_day)
        