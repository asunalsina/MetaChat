import numpy as np
import string, json, random, re
from datetime import datetime
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
            button_list = button_list = sentences['buttons']['profile']
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
        if user_message.lower() == sentences['buttons']['profile'][0][0].lower():
            bot_message = sentences['profile_data'][0][0]
            button_list = button_list = sentences['buttons']['yes_no']
            rm = ReplyKeyboardMarkup(button_list)

        # Set reminders
        elif user_message.lower() == sentences['buttons']['profile'][2][0].lower():
            bot_message = sentences['profile_data'][0][2]
            button_list = sentences['buttons']['reminder']
            rm = ReplyKeyboardMarkup(button_list)

    elif stage == 3:
        # Delete data
        if user_message.lower() == 'yes':
            mongobase.delete_data(chat_id)
            bot_message = sentences['profile_data'][1]
            rm = ReplyKeyboardRemove()
            meta_conversation = False

        elif user_message.lower() == 'no':
            bot_message = 'Okay!'
            rm = ReplyKeyboardRemove()
            meta_conversation = False

        # Manage reminders
        # Daily
        elif user_message.lower() == sentences['buttons']['reminder'][0][0].lower():
            mongobase.set_reminder(chat_id, 'daily')
            bot_message = 'Your preferences have been saved'
            rm = ReplyKeyboardRemove()
            meta_conversation = False        

        # Weekly
        elif user_message.lower() == sentences['buttons']['reminder'][1][0].lower():
            mongobase.set_reminder(chat_id, 'weekly')
            bot_message = 'Your preferences have been saved'
            rm = ReplyKeyboardRemove()
            meta_conversation = False        

        # No reminders
        elif user_message.lower() == sentences['buttons']['reminder'][2][0].lower():
            mongobase.set_reminder(chat_id, 'no')
            bot_message = 'Your preferences have been saved'
            rm = ReplyKeyboardRemove()
            meta_conversation = False        

    return rm, bot_message, meta_conversation

### PHASE 2 ###
# Talk about what is happening conversation
def feelings_talk(stage, meta_conversation, user_message, chat_id, entity, sentences = sentences):
    if stage == 0:
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
        bot_message = sentences['reconnect_present'][stage][np.random.randint(len(sentences['reconnect_present'][stage]))]
        button_list = sentences['buttons']['yes_no']
        rm = ReplyKeyboardMarkup(button_list)

    elif stage == 1:
        if user_message.lower() == 'yes':
            lm = mongobase.get_last_message(chat_id)

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
    keywords = ['sleep', 'die', 'kill', 'nothing', 'suicide']
    entity_name = entity.get('name')
    if stage == 0:
        if entity_name == 'quadrant_two':
            bot_message = sentences['suggest_activity'][stage][0]
        elif entity_name == 'quadrant_three':
            bot_message = sentences['suggest_activity'][stage][1]
        button_list = sentences['buttons']['yes_no']
        rm = ReplyKeyboardMarkup(button_list)

    elif stage == 1:
        if user_message.lower() == 'yes':
            hobby = user_hobby(entity_name, chat_id)
            bot_message = sentences['suggest_activity'][stage][0] %(hobby)
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
    
    elif selected_conversation == 1:
        rm, bot_message, meta_conversation = feelings_reconnect(stage, meta_conversation, user_message, chat_id, entity, sentences = sentences)
    
    elif selected_conversation == 2:
        rm, bot_message, meta_conversation = feelings_suggest(stage, meta_conversation, user_message, chat_id, entity, sentences = sentences)

    return rm, bot_message, meta_conversation

def user_phase_two(stage, meta_conversation, user_message, chat_id, sentences = sentences):
    if stage == 0:
        bot_message = sentences['user_phase_2'][stage]
        button_list = sentences['buttons']['data_2']
        rm = ReplyKeyboardMarkup(button_list)

    elif stage == 1:
        # Manage my data
        if user_message.lower() == sentences['buttons']['data_2'][0][0].lower():
            bot_message = sentences['user_phase_2'][stage][0]
            button_list = button_list = sentences['buttons']['profile']
            rm = ReplyKeyboardMarkup(button_list)
        # Why are you asking me this?
        elif user_message.lower() == sentences['buttons']['data_2'][1][0].lower():
            last_emotion = mongobase.last_emotion(chat_id, 'get')
            if last_emotion:
                bot_message = sentences['user_phase_2'][stage][1] %(last_emotion[0], last_emotion[1])
            else:
                bot_message = sentences['user_data'][stage][2]
            rm = ReplyKeyboardRemove()
            meta_conversation = False
        # Know how my data is used
        elif user_message.lower() == sentences['buttons']['data_2'][2][0].lower():
            bot_message = sentences['user_phase_2'][stage][2]
            rm = ReplyKeyboardRemove()
            meta_conversation = False

    elif stage == 2:
        # Delete data
        if user_message.lower() == sentences['buttons']['profile'][0][0].lower():
            bot_message = sentences['profile_data'][0][0]
            button_list = button_list = sentences['buttons']['yes_no']
            rm = ReplyKeyboardMarkup(button_list)

        # Set reminders
        elif user_message.lower() == sentences['buttons']['profile'][2][0].lower():
            bot_message = sentences['profile_data'][0][2]
            button_list = sentences['buttons']['reminder']
            rm = ReplyKeyboardMarkup(button_list)

    elif stage == 3:
        # Delete data
        if user_message.lower() == 'yes':
            mongobase.delete_data(chat_id)
            bot_message = sentences['profile_data'][1]
            rm = ReplyKeyboardRemove()
            meta_conversation = False

        elif user_message.lower() == 'no':
            bot_message = 'Okay!'
            rm = ReplyKeyboardRemove()
            meta_conversation = False

        # Manage reminders
        # Daily
        elif user_message.lower() == sentences['buttons']['reminder'][0][0].lower():
            print(f'Here {chat_id}')
            mongobase.set_reminder(chat_id, 'daily')
            bot_message = 'Your preferences have been saved'
            rm = ReplyKeyboardRemove()
            meta_conversation = False        

        # Weekly
        elif user_message.lower() == sentences['buttons']['reminder'][1][0].lower():
            mongobase.set_reminder(chat_id, 'weekly')
            bot_message = 'Your preferences have been saved'
            rm = ReplyKeyboardRemove()
            meta_conversation = False        

        # No reminders
        elif user_message.lower() == sentences['buttons']['reminder'][2][0].lower():
            mongobase.set_reminder(chat_id, 'no')
            bot_message = 'Your preferences have been saved'
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

def user_hobby(entity_name, chat_id):
    # Quadrant 1 -> positive valence, high activation
    # Quadrant 2 -> negative valence, high activation
    # Quadrant 3 -> negative valence, low activation
    # Quadrant 4 -> positive valence, low activation
    user_map = mongobase.get_user_map(chat_id)
    print(user_map)
    # Check the time and classify it
    time_now = datetime.now().strftime("%H:%M")
    if time_now >= '04:00' and time_now < '12:00':
        time_day = 'morning'
    elif time_now >= '12:00' and time_now < '20:00':
        time_day = 'afternoon'
    else:
        time_day = 'evening'

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
    # Create a dataframe and group by quadrant-time
    user_map.pop('activation')
    user_map.pop('valence')
    user_map['quadrant'] = quadrant
    user_map_df = pd.DataFrame(user_map)
    pairs = user_map_df.groupby(['quadrant', 'time', 'activity']).size()
    pairs_df = pairs.to_frame(name = 'size').reset_index()

    quadrant_pairs = pairs_df.loc[pairs_df['quadrant'] == entity_name]

    if len(quadrant_pairs) != 0:
        quadrant_time_pairs = quadrant_pairs.loc[quadrant_pairs['time'] == time_day]
        if len(quadrant_time_pairs) != 0:
            max_pairs = quadrant_time_pairs.loc[quadrant_time_pairs['size'] == quadrant_time_pairs['size'].max()].reset_index(drop = True)
            if len(max_pairs) > 1:
                hobby = str(max_pairs['activity'][np.random.randint(len(max_pairs))])
            else:
                hobby = str(max_pairs['activity'][0])
        else:
            max_pairs = quadrant_time_pairs.loc[quadrant_pairs['size'] == quadrant_pairs['size'].max()].reset_index(drop = True)
            if len(max_pairs) > 1:
                hobby = str(max_pairs['activity'][np.random.randint(len(max_pairs))])
            else:
                hobby = str(max_pairs['activity'][0])

    else:    
        quadrant_pairs = pairs_df.loc[pairs_df['quadrant'].isin('quadrant_one', 'quadrant_four')]
        if len(quadrant_pairs) != 0:
            quadrant_time_pairs = quadrant_pairs.loc[quadrant_pairs['time'] == time_day]
            if len(quadrant_time_pairs) != 0:
                max_pairs = quadrant_time_pairs.loc[quadrant_time_pairs['size'] == quadrant_time_pairs['size'].max()].reset_index(drop = True)
                if len(max_pairs) > 1:
                    hobby = str(max_pairs['activity'][np.random.randint(len(max_pairs))])
                else:
                    hobby = str(max_pairs['activity'][0])
            else:
                max_pairs = quadrant_time_pairs.loc[quadrant_pairs['size'] == quadrant_pairs['size'].max()].reset_index(drop = True)
                if len(max_pairs) > 1:
                    hobby = str(max_pairs['activity'][np.random.randint(len(max_pairs))])
                else:
                    hobby = str(max_pairs['activity'][0])
        else:
            hobby = get_hobbies_list(self, number_hobbies = 1)
    return hobby

