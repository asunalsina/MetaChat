import numpy as np
import string, json
from database.mongobase import mongodb_database
import pandas as pd

from telegram import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove

with open('rulebased/rule_sentences.json') as file:
    sentences = json.loads(file.read())

mongobase = mongodb_database()

### PHASE 1 ###
def feelings_conversation(stage, meta_conversation, user_message, chat_id, sentences = sentences):
    if stage == 0:
        clean_message = ''.join([word for word in user_message if word not in string.punctuation])
        clean_message = clean_message.split()
        suggestion = [word for word in clean_message if any([word for keywords in sentences['suggestion_keywords'] if word.lower() == keywords])]
        
        if len(suggestion) > 0:
            bot_message = f'You could try {", ".join([exercise.lower() for exercise in sentences["anxiety_exercises"]])}, etc. Do you want more information?'
            button_list = sentences['buttons']['yes_no']
            rm = ReplyKeyboardMarkup(button_list)

        else:
            bot_message = sentences['feelings'][stage]
            button_list = sentences['buttons']['yes_no']
            rm = ReplyKeyboardMarkup(button_list)

    elif stage == 1:
        if user_message.lower() == 'yes':
            bot_message = sentences['feelings'][stage]
            button_list = sentences['buttons']['distress']
            rm = ReplyKeyboardMarkup(button_list)
        else:
            bot_message = 'Okay!'
            rm = ReplyKeyboardRemove()
            meta_conversation = False


    elif stage == 2:
        # Feelings conversation
        if any(True for button in sentences['buttons']['distress'] if user_message.lower() == button[0].lower() and user_message.lower() != 'none'):
            # Save user map data
            mongobase.user_map(chat_id, user_message.lower(), 'emotion')
            
            bot_message = sentences['feelings'][stage]
            rm = ReplyKeyboardRemove()

        elif user_message.lower() == 'none':
            bot_message = 'Okay!'
            rm = ReplyKeyboardRemove()
            meta_conversation = False

        # Suggestions conversation
        elif user_message.lower() == 'yes':
            bot_message = 'Select one exercise'
            button_list = [[button] for button in sentences['anxiety_exercises']]
            rm = ReplyKeyboardMarkup(button_list)

        elif user_message.lower() == 'no':
            bot_message = 'Okay!'
            rm = ReplyKeyboardRemove()
            meta_conversation = False

    elif stage == 3:
        # Feelings conversation
        if not any([True for exercise in sentences['anxiety_exercises'] if exercise.lower() == user_message.lower()]):
            # Classify the reason in one of the categories
            reason = classify_reason(user_message.lower())
            if reason:
                # Save user map data
                mongobase.user_map(chat_id, reason, 'reason')
                mongobase.user_map(chat_id, 'nothing', 'activity')

                bot_message = sentences['feelings'][stage]
                button_list = sentences['buttons']['yes_no']
                rm = ReplyKeyboardMarkup(button_list)

            # If the reason cannot be classified ask the user
            else:
                bot_message = 'In which category would it fit?'
                button_list = sentences['buttons']['reason_categories']
                rm = ReplyKeyboardMarkup(button_list)

        # Suggestions conversation
        else:
            bot_message = sentences['exercises_instructions'][user_message.lower().split()[0]]
            rm = ReplyKeyboardRemove()
            meta_conversation = False

    elif stage == 4:
        # Reason categories
        if user_message.lower() in ['grief', 'job', 'relationship', 'money', 'studies', 'health']:
            mongobase.user_map(chat_id, user_message.lower(), 'reason')
            mongobase.user_map(chat_id, 'nothing', 'activity')
            
            bot_message = sentences['feelings'][stage-1]
            button_list = sentences['buttons']['yes_no']
            rm = ReplyKeyboardMarkup(button_list)

        else:
            if user_message.lower() == 'yes':
                bot_message = sentences['feelings'][stage]
                button_list = [[button] for button in sentences['anxiety_exercises']]
                rm = ReplyKeyboardMarkup(button_list)

            else:
                bot_message = 'Okay!'
                rm = ReplyKeyboardRemove()    
                meta_conversation = False

    elif stage == 5:
        if user_message.lower() in sentences['anxiety_exercises']:
            bot_message = sentences['exercises_instructions'][user_message.lower().split()[0]]
            rm = ReplyKeyboardRemove()
            meta_conversation = False

        else:
            if user_message.lower() == 'yes':
                bot_message = sentences['feelings'][stage-1]
                button_list = [[button] for button in sentences['anxiety_exercises']]
                rm = ReplyKeyboardMarkup(button_list)

            else:
                bot_message = 'Okay!'
                rm = ReplyKeyboardRemove()    
                meta_conversation = False


    elif stage == 6:
        bot_message = sentences['exercises_instructions'][user_message.lower().split()[0]]
        rm = ReplyKeyboardRemove()
        meta_conversation = False


    return rm, bot_message, meta_conversation, stage

def current_conversation(stage, meta_conversation, user_message, chat_id, sentences = sentences):
    if stage == 0:
        bot_message = sentences['current'][stage]
        button_list = button_list = sentences['buttons']['yes_no']
        rm = ReplyKeyboardMarkup(button_list)

    elif stage == 1:
        if user_message.lower() == 'yes':
            bot_message = sentences['current'][stage]
            button_list = sentences['buttons']['distress'][:-1]
            rm = ReplyKeyboardMarkup(button_list)

        else:
            bot_message = 'Have a nice day!'
            rm = ReplyKeyboardRemove()
            meta_conversation = False

    elif stage == 2:        
        # Save user map data
        mongobase.user_map(chat_id, user_message.lower(), 'emotion')
        mongobase.user_map(chat_id, 'coronavirus', 'reason')
        mongobase.user_map(chat_id, 'nothing', 'activity')
        
        bot_message = sentences['current'][stage][np.random.randint(len(sentences['current'][stage]))]
        rm = ReplyKeyboardRemove()
        meta_conversation = False

    return rm, bot_message, meta_conversation, stage

def workings_conversation(stage, meta_conversation, user_message, chat_id, entity, phase, sentences = sentences):
    if 'meta' == entity.get('name'):
        if phase == 1:
            rm, bot_message, meta_conversation, stage = user_conversation(stage, meta_conversation, user_message, chat_id, sentences = sentences)
        elif phase == 2:
            rm, bot_message, meta_conversation, stage = user_phase_2(stage, meta_conversation, user_message, chat_id, sentences = sentences)
        elif phase == 3:
            rm, bot_message, meta_conversation, stage = user_phase_3(stage, meta_conversation, user_message, chat_id, sentences = sentences)
    elif 'malfunction' == entity.get('name'):
        rm, bot_message, meta_conversation, stage = malfunction_conversation(stage, meta_conversation, user_message, chat_id, sentences = sentences)

    return rm, bot_message, meta_conversation, stage

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

    return rm, bot_message, meta_conversation, stage

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

    return rm, bot_message, meta_conversation, stage

### PHASE 2 ###
def feelings_phase_2(stage, meta_conversation, user_message, chat_id, entity, sentences = sentences):
    if stage == 0:
        reason, emotion = get_reason_emotion(chat_id, entity)
        mongobase.last_emotion(chat_id, 'save', [emotion, reason])
        bot_message = sentences['feelings_phase_two'][stage] %(emotion, reason)
        button_list = sentences['buttons']['yes_no']
        rm = ReplyKeyboardMarkup(button_list)

    elif stage == 1:
        if user_message.lower() == 'yes':
            bot_message = sentences['feelings_phase_two'][stage][0]
            rm = ReplyKeyboardRemove()

        else:
            bot_message = sentences['feelings_phase_two'][stage][1]
            button_list = sentences['buttons']['distress'][:-1]
            rm = ReplyKeyboardMarkup(button_list)

    elif stage == 2:
        if any(True for element in sentences['buttons']['distress'] if element[0].lower() == user_message.lower()):
            mongobase.user_map(chat_id, user_message.lower(), 'emotion')
            bot_message = sentences['feelings_phase_two'][stage][0]
            button_list = sentences['buttons']['reason_categories']
            button_list.append(['Coronavirus'])
            rm = ReplyKeyboardMarkup(button_list)

        else:
            # Save activity
            mongobase.user_map(chat_id, user_message.lower(), 'activity')
            bot_message = sentences['feelings_phase_two'][stage][1]
            rm = {}
            meta_conversation = False

    elif stage == 3:
        mongobase.user_map(chat_id, user_message.lower(), 'reason')
        bot_message = sentences['feelings_phase_two'][stage]
        rm = ReplyKeyboardRemove()
        meta_conversation = False

    return rm, bot_message, meta_conversation, stage

def user_phase_2(stage, meta_conversation, user_message, chat_id, sentences = sentences):
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

    return rm, bot_message, meta_conversation, stage

### PHASE 3 ###
def feelings_phase_3(stage, meta_conversation, user_message, chat_id, entity, sentences = sentences):
    common_activities = mongobase.get_hobbies_list()
    if stage == 0:
        reason, emotion, activities = get_emotion_activity(chat_id, entity)
        mongobase.last_activity(chat_id, 'save', [emotion, activities])
        bot_message = sentences['feelings_phase_three'][stage] %(emotion)
        button_list = [[activity] for activity in activities if activity.lower() != 'nothing']
        
        if len(button_list) < 3:
            possible_activities = [activity for activity in common_activities if activity.lower() != button_list[0][0].lower()]
            index = random.sample(range(0, len(possible_activities)), (3-len(button_list)))
            selected_activities = [[possible_activities[i].capitalize()] for i in index]
            button_list.extend(selected_activities)
            button_list.append([f"I'm not {emotion}"])

        elif len(button_list) > 3:
            index = random.sample(range(0, len(button_list)), 3)
            button_list = [button_list[i] for i in index]
            button_list.append(["I'm not feeling that way"])
        rm = ReplyKeyboardMarkup(button_list)

    elif stage == 1:
        if user_message == "I'm not feeling that way":
            bot_message = 'How are you feeling?'
            button_list = sentences['buttons']['distress']
            rm = ReplyKeyboardMarkup(button_list)
        else:
            bot_message = sentences['feelings_phase_three'][stage]
            rm = ReplyKeyboardRemove()
            meta_conversation = False

    elif stage == 2:
        mongobase.user_map(chat_id, user_message.lower(), 'emotion')
        if user_message.lower() == 'none':
            bot_message = 'Okay!'
            rm = ReplyKeyboardRemove()
            meta_conversation = False
        else:
            bot_message = 'What is causing it?'
            button_list = sentences['buttons']['reason_categories']
            button_list.append('Coronavirus')
            rm = ReplyKeyboardMarkup(button_list)

    elif stage == 3:
        mongobase.user_map(chat_id, user_message.lower(), 'reason')
        bot_message = 'What activity do you feel like doing?'
        rm = ReplyKeyboardRemove()

    elif stage == 4:
        mongobase.user_map(chat_id, user_message.lower(), 'activity')
        bot_message = 'Cool choice!'
        rm = {}
        meta_conversation = False

    return rm, bot_message, meta_conversation, stage

def user_phase_3(stage, meta_conversation, user_message, chat_id, sentences = sentences):
    if stage == 0:
        bot_message = sentences['user_phase_3'][stage]
        button_list = sentences['buttons']['data_3']
        rm = ReplyKeyboardMarkup(button_list)

    elif stage == 1:
        # Manage my data
        if user_message.lower() == sentences['buttons']['data_3'][0][0].lower():
            bot_message = sentences['user_phase_3'][stage][0]
            button_list = button_list = sentences['buttons']['profile']
            rm = ReplyKeyboardMarkup(button_list)
        # Why are you asking me this?
        elif user_message.lower() == sentences['buttons']['data_3'][1][0].lower():
            last_activity = mongobase.last_activity(chat_id, 'get')
            if last_activity:
                activities = [act.lower() for act in last_activity[1] if a.lower() != 'nothing']
                if len(activities) == 1:
                    bot_message = sentences['user_phase_3'][stage][1] %(last_activity[0], activities[0])
                # More than one activity
                else:
                    bot_message = sentences['user_phase_3'][stage][1] %(last_activity[0], ', '.join(activities))
            else:
                bot_message = sentences['user_data'][stage][2]
            rm = ReplyKeyboardRemove()
            meta_conversation = False
        # Know how my data is used
        elif user_message.lower() == sentences['buttons']['data_3'][2][0].lower():
            bot_message = sentences['user_phase_3'][stage][2]
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

    return rm, bot_message, meta_conversation, stage

# Useful functions
def classify_reason(sentence):
    keywords = ['grief', 'job', 'relationship', 'money', 'studies', 'health']

    sentence_list = sentence.split(' ')
    reason = list(set(sentence_list).intersection(keywords))

    if reason:
        return reason[0]
    else:
        reason = False
        return reason

def get_reason_emotion(chat_id, entity):
    map_pairs = mongobase.get_map_pairs(chat_id, 'reason')
    map_pairs = pd.DataFrame(map_pairs)
    
    if entity:
        emotion = entity.get('name')    
        if emotion in map_pairs['emotion'].values:
            emotion_pairs = map_pairs.loc[map_pairs['emotion'] == emotion]
            max_pairs = emotion_pairs.loc[emotion_pairs['size'] == emotion_pairs['size'].max()].reset_index(drop = True)
            if len(max_pairs) == 1:
                reason = max_pairs['reason'][0]
            else:
                reason = max_pairs['reason'][np.random.randint(len(max_pairs))]
        
        elif emotion == 'coronavirus':
            reason = 'coronavirus'
            emotion_pairs = map_pairs.loc[map_pairs['reason'] == reason]
            max_pairs = emotion_pairs.loc[emotion_pairs['size'] == emotion_pairs['size'].max()].reset_index(drop = True)
            if len(max_pairs) == 1:
                emotion = max_pairs['emotion'][0]
            else:
                emotion = max_pairs['emotion'][np.random.randint(len(max_pairs))]

        else:
            possible_reasons = map_pairs.loc[map_pairs['size'] == map_pairs['size'].max()].reset_index(drop = True)

            if len(possible_reasons) == 1:
                reason = possible_reasons['reason'][0]
            else:
                reason = possible_reasons['reason'][np.random.randint(len(possible_reasons))]
    
    else:
        max_pairs = map_pairs.loc[map_pairs['size'] == map_pairs['size'].max()].reset_index(drop = True)
        if len(max_pairs) == 1:
            emotion = max_pairs['emotion'][0]
            reason = max_pairs['reason'][0]
        else:
            emotion = max_pairs['emotion'][np.random.randint(len(max_pairs))]
            reason = max_pairs['reason'][np.random.randint(len(max_pairs))]

    return reason, emotion

def get_emotion_activity(chat_id, entity):
    map_pairs = mongobase.get_map_pairs(chat_id, 'activity')
    map_pairs = pd.DataFrame(map_pairs)

    if entity:
        emotion = entity.get('name')    

        if emotion in map_pairs['emotion'].values:
            emotion_pairs = map_pairs.loc[map_pairs['emotion'] == emotion]
            max_pairs = emotion_pairs.loc[emotion_pairs['size'] == emotion_pairs['size'].max()].reset_index(drop = True)

            if len(max_pairs) == 1:
                reason = max_pairs['reason'][0]
            else:
                reason = max_pairs['reason'][np.random.randint(len(max_pairs))]

            activities = list(emotion_pairs.loc[emotion_pairs['reason'] == reason]['activity'])
        
        elif emotion == 'coronavirus':
            reason = 'coronavirus'
            emotion_pairs = map_pairs.loc[map_pairs['reason'] == reason]
            max_pairs = emotion_pairs.loc[emotion_pairs['size'] == emotion_pairs['size'].max()].reset_index(drop = True)
            if len(max_pairs) == 1:
                emotion = max_pairs['emotion'][0]
            else:
                emotion = max_pairs['emotion'][np.random.randint(len(max_pairs))]
            activities = list(emotion_pairs.loc[emotion_pairs['reason'] == reason]['activity'])

        else:
            possible_reasons = map_pairs.loc[map_pairs['size'] == map_pairs['size'].max()].reset_index(drop = True)

            if len(possible_reasons) == 1:
                reason = max_pairs['reason'][0]
            else:
                reason = possible_reasons['reason'][np.random.randint(len(possible_reasons))]
        
            emotion_pairs = map_pairs.loc[map_pairs['emotion'] == emotion]
            activities = list(emotion_pairs.loc[emotion_pairs['reason'] == reason]['activity'])
    
    else:
        max_pairs = map_pairs.loc[map_pairs['size'] == map_pairs['size'].max()].reset_index(drop = True)

        if len(max_pairs) == 1:
            emotion = max_pairs['emotion'][0]
            reason = max_pairs['reason'][0]
        else:
            emotion = max_pairs['emotion'][np.random.randint(len(max_pairs))]
            reason = max_pairs['reason'][np.random.randint(len(max_pairs))]

        emotion_pairs = map_pairs.loc[map_pairs['emotion'] == emotion]
        activities = list(emotion_pairs.loc[emotion_pairs['reason'] == reason]['activity'])

    return reason, emotion, activities

