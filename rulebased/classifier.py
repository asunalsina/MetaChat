import random, calendar, json
import rulebased.metabot as metabot

from datetime import datetime
from wit import Wit

from gpt2bot.decoder import generate_response
from database.mongobase import mongodb_database

with open('tokens.json') as f:
    token_file = json.loads(f.read())

# Create client
token = token_file["wit_token"]
client = Wit(token)
mongobase = mongodb_database()

def check_utterance(turn, metaconversation, call, entity, chat_id, client = client):
    reply = client.message(turn)

    if len(reply['intents']) != 0 and not metaconversation:
        # feelings, current_situation or chatbot_workings
        phase = mongobase.phase(chat_id, 'get')

        call = reply['intents'][0]['name']
        metaconversation = True
        entities = reply['entities']
        if entities:
            [(k, v)] = entities.items()
            entity = v[0]
        else:
            entity = entities

        if phase == 2:
            if entity.get('name') == 'quadrant_one' or entity.get('name') == 'quadrant_four':
                metaconversation = False

    return call, metaconversation, entity

def bot_response(num_samples, model, tokenizer, history, config, mmi_model, mmi_tokenizer):
    bot_messages = generate_response(
        model, 
        tokenizer, 
        history, 
        config, 
        mmi_model=mmi_model, 
        mmi_tokenizer=mmi_tokenizer)

    rm = {}
    if num_samples == 1:
        bot_message = bot_messages[0]
    else:
        bot_message = random.choice(bot_messages)

    return rm, bot_message

def meta_response(turn, call, metaconversation, stage, chat_id, entity):
    phase = mongobase.phase(chat_id, 'get')

    if phase == 1:
        if call == 'feelings':
            rm, bot_message, metaconversation = metabot.feelings_phase_one(stage, metaconversation, turn, chat_id)
            if metaconversation:
                stage += 1
            else:
                stage = 0

        elif call == 'chatbot_workings':
            rm, bot_message, metaconversation = metabot.workings_conversation(stage, metaconversation, turn, chat_id, entity, phase)
            if metaconversation:
                stage += 1
            else:
                stage = 0

    elif phase == 2:
        if call == 'feelings':
            rm, bot_message, metaconversation = metabot.feelings_phase_two(stage, metaconversation, turn, chat_id, entity)
            if metaconversation:
                stage += 1
            else:
                selected_conversation = 3
                mongobase.get_selected_conversation(chat_id, 'set')
                stage = 0

        elif call == 'chatbot_workings':
            rm, bot_message, metaconversation = metabot.workings_conversation(stage, metaconversation, turn, chat_id, entity, phase)
            if metaconversation:
                stage += 1
            else:
                stage = 0

    return rm, bot_message, metaconversation, stage


def reply_message(turn, num_samples, model, tokenizer, history, config, mmi_model, 
    mmi_tokenizer, metaconversation, stage, call, entity, chat_id):

    turn  = turn[0]

    call, metaconversation, entity = check_utterance(turn, metaconversation, call, entity, chat_id)

    if metaconversation:
        rm, bot_message, metaconversation, stage = meta_response(turn, call, metaconversation, stage, chat_id, entity)

    else:
        rm, bot_message = bot_response(num_samples, model, tokenizer, history, config, mmi_model, mmi_tokenizer)

    return rm, bot_message, metaconversation, stage, call, entity


def save_utterance(turn, chat_id, field):
    message_time = datetime.now().strftime("%H:%M:%S")
    message_date = datetime.now().strftime("%Y/%m/%d")
    message_day = calendar.day_name[datetime.today().weekday()]
    message = ' - '.join([field, message_day, message_date, message_time, turn])
    data = {'conversation': message}

    mongobase.insert_data(data, chat_id, multiple = True)

