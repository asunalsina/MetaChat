import numpy as np
import string, json
import database.mongobase as mongobase

from telegram import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove

with open('rulebased/rule_sentences.json') as file:
    sentences = json.loads(file.read())

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
            button_list = sentences['buttons']['feelings']
            rm = ReplyKeyboardMarkup(button_list)

    elif stage == 1:
        # Feelings conversation
        if user_message.lower() == 'stressed' or user_message.lower() == 'depressed':
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

    elif stage == 2:
        # Feelings conversation
        if not any([True for exercise in sentences['anxiety_exercises'] if exercise.lower() == user_message.lower()]):
            # Classify the reason in one of the categories
            reason = classify_reason(user_message.lower())
            if reason:
                # Save user map data
                mongobase.user_map(chat_id, reason, 'reason')

                # Check if the user has some hobbies saved in their profile
                hobbies = mongobase.hobbies_df(chat_id)
                if hobbies:
                    bot_message = sentences['feelings'][stage][np.random.randint(len(sentences['feelings'][stage]))]
                    if bot_message == sentences['feelings'][stage][1]:
                        bot_message = bot_message %(mongobase.get_hobby(chat_id).lower())
                        rm = {}
                        meta_conversation = False
                    else:
                        button_list = sentences['buttons']['yes_no']
                        rm = ReplyKeyboardMarkup(button_list)
                else:
                    bot_message = 'Tell me some of your hobbies (please separate them with a comma)'
                    rm = {}

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

    elif stage == 3:
        # Reason categories
        if user_message.lower() in ['death', 'job', 'relationship', 'money', 'university', 'health']:
            mongobase.user_map(chat_id, user_message.lower(), 'reason')

            # Check if the user has some hobbies saved in their profile
            hobbies = mongobase.hobbies_df(chat_id)
            if hobbies:
                print('In here')
                bot_message = sentences['feelings'][stage-1][np.random.randint(len(sentences['feelings'][stage-1]))]
                if bot_message == sentences['feelings'][stage-1][1]:
                    bot_message = bot_message %(mongobase.get_hobby(chat_id).lower())
                    rm = ReplyKeyboardRemove()
                    meta_conversation = False
                else:
                    button_list = sentences['buttons']['yes_no']
                    rm = ReplyKeyboardMarkup(button_list)
            else:
                bot_message = 'Tell me some of your hobbies (please separate them with a comma)'
                rm = ReplyKeyboardRemove()

        else:
            # Check if the user has some hobbies saved in their profile
            hobbies = mongobase.hobbies_df(chat_id)
        
            if hobbies:
                if user_message.lower() == 'yes':
                    bot_message = sentences['feelings'][stage]
                    button_list = [[button] for button in sentences['anxiety_exercises']]
                    rm = ReplyKeyboardMarkup(button_list)

                else:
                    bot_message = 'Okay!'
                    rm = ReplyKeyboardRemove()    
                    meta_conversation = False

            else:
                mongobase.save_hobbies(user_message, chat_id)
                bot_message = 'Thank you'
                rm = {}
                meta_conversation = False

    elif stage == 4:
        if user_message.lower() in sentences['anxiety_exercises']:
            bot_message = sentences['exercises_instructions'][user_message.lower().split()[0]]
            rm = ReplyKeyboardRemove()
            meta_conversation = False

        else:
            # Check if the user has some hobbies saved in their profile
            hobbies = mongobase.hobbies_df(chat_id)
        
            if hobbies:
                if user_message.lower() == 'yes':
                    bot_message = sentences['feelings'][stage-1]
                    button_list = [[button] for button in sentences['anxiety_exercises']]
                    rm = ReplyKeyboardMarkup(button_list)

                else:
                    bot_message = 'Okay!'
                    rm = ReplyKeyboardRemove()    
                    meta_conversation = False

            else:
                mongobase.save_hobbies(user_message, chat_id)
                bot_message = 'Thank you'
                rm = {}
                meta_conversation = False

    elif stage == 5:
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
            button_list = sentences['buttons']['distress']
            rm = ReplyKeyboardMarkup(button_list)

        else:
            bot_message = 'Have a nice day!'
            rm = ReplyKeyboardRemove()
            meta_conversation = False

    elif stage == 2:        
        rm = ReplyKeyboardRemove()
        
        # Save user map data
        mongobase.user_map(chat_id, user_message.lower(), 'emotion')
        mongobase.user_map(chat_id, 'coronavirus', 'reason')

        # Check if the user has some hobbies saved in their profile
        hobbies = mongobase.hobbies_df(chat_id)
        if hobbies:
            bot_message = sentences['current'][stage][np.random.randint(len(sentences['current'][stage]))]
            if bot_message == sentences['current'][stage][3]:
                bot_message = bot_message %(mongobase.get_hobby(chat_id).lower())
            meta_conversation = False

        else:
            bot_message = 'Tell me some of your hobbies (please separate them with a comma)'

    elif stage == 3:
        mongobase.save_hobbies(user_message, chat_id)
        bot_message = 'Thanks!'
        rm = {}
        meta_conversation = False


    return rm, bot_message, meta_conversation, stage

def workings_conversation(stage, meta_conversation, user_message, chat_id, entity, sentences = sentences):

    if 'meta:meta' in entity:
        rm, bot_message, meta_conversation, stage = user_conversation(stage, meta_conversation, user_message, chat_id, sentences = sentences)
    elif 'malfunction:malfunction' in entity:
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
        if not mongobase.metaquestion(chat_id, 'keys'):
            button_list = sentences['buttons']['data']
        else:
            button_list = sentences['buttons']['new_data']
        rm = ReplyKeyboardMarkup(button_list)

    elif stage == 1:
        # Manage my data
        if user_message.lower() == sentences['buttons']['data'][0][0].lower():
            bot_message = sentences['user_data'][stage][0]
            button_list = button_list = sentences['buttons']['profile']
            rm = ReplyKeyboardMarkup(button_list)
        
        # Know how my data is used
        elif user_message.lower() == sentences['buttons']['data'][1][0].lower():
            mongobase.metaquestion(chat_id)
            bot_message = sentences['user_data'][stage][1]
            rm = ReplyKeyboardRemove()
            meta_conversation = False

        elif user_message.lower() == sentences['buttons']['new_data'][1][0].lower():
            bot_message = sentences['user_data'][stage][2]
            rm = ReplyKeyboardRemove()
            meta_conversation = False

        elif user_message.lower() == sentences['buttons']['new_data'][2][0].lower():
            bot_message = sentences['user_data'][stage][1]
            rm = ReplyKeyboardRemove()
            meta_conversation = False

    elif stage == 2:
        # Delete data
        if user_message.lower() == sentences['buttons']['profile'][0][0].lower():
            bot_message = sentences['profile_data'][0][0]
            button_list = button_list = sentences['buttons']['yes_no']
            rm = ReplyKeyboardMarkup(button_list)

        # Manage hobbies
        elif user_message.lower() == sentences['buttons']['profile'][1][0].lower():
            bot_message = sentences['profile_data'][0][1]
            button_list = sentences['buttons']['hobbies']
            rm = ReplyKeyboardMarkup(button_list)

        # Set reminders
        elif user_message.lower() == sentences['buttons']['profile'][2][0].lower():
            bot_message = sentences['profile_data'][0][2]
            button_list = sentences['buttons']['reminder']
            rm = ReplyKeyboardMarkup(button_list)

    elif stage == 3:
        # Delete data
        if user_message.lower() == 'yes':
            mongobase.delete_data(chat_id, 'user')
            bot_message = sentences['profile_data'][1]
            rm = ReplyKeyboardRemove()
            meta_conversation = False

        elif user_message.lower() == 'no':
            bot_message = 'Okay!'
            rm = ReplyKeyboardRemove()
            meta_conversation = False

        # Manage hobbies
        # Add
        elif user_message.lower() == sentences['buttons']['hobbies'][0][0].lower():
            bot_message = 'Tell me your hobbies'
            rm = ReplyKeyboardRemove()

        # Delete
        elif user_message.lower() == sentences['buttons']['hobbies'][1][0].lower():
            mongobase.delete_data(chat_id, 'hobbies')
            bot_message = 'Your hobbies have been deleted'
            rm = ReplyKeyboardRemove()
            meta_conversation = False

        # Saved
        elif user_message.lower() == sentences['buttons']['hobbies'][2][0].lower():
            saved_hobbies = mongobase.get_hobby(chat_id, True)
            if len(saved_hobbies) > 0:
                bot_message = f'These are the hobbies {", ".join(saved_hobbies).lower()}'
            else:
                bot_message = 'There are no hobbies saved in your profile'
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

    elif stage == 4:
        mongobase.save_hobbies(user_message, chat_id)
        bot_message = 'Your hobbies have been added'
        rm = {}
        meta_conversation = False

    return rm, bot_message, meta_conversation, stage



# Useful functions
def classify_reason(sentence):
    keywords = ['death', 'job', 'relationship', 'money', 'university', 'health']

    sentence_list = sentence.split(' ')
    reason = list(set(sentence_list).intersection(keywords))

    if reason:
        return reason[0]
    else:
        reason = False
        return reason