import random, calendar, json
import rulebased.metabot as metabot

from datetime import datetime
from wit import Wit

from gpt2bot.decoder import generate_response
from database.mongobase import insert_data, get_data, increment_field, get_phase

with open('tokens.json') as f:
    token_file = json.loads(f.read())

# Create client
token = token_file["wit_token"]
client = Wit(token)

def check_utterance(turn, metaconversation, call, entity, client = client):
    reply = client.message(turn)

    if len(reply['intents']) != 0 and not metaconversation:
        # feelings, current_situation or chatbot_workings
        call = reply['intents'][0]['name']
        metaconversation = True
        entities = reply['entities']
        if entities:
            [(k, v)] = entities.items()
            entity = v[0]
        else:
            entity = entities

    return call, metaconversation, entity

def bot_response(num_samples, model, tokenizer, history, config, mmi_model, mmi_tokenizer):
    bot_messages = generate_response(
        model, 
        tokenizer, 
        history, 
        config, 
        mmi_model=mmi_model, 
        mmi_tokenizer=mmi_tokenizer
    )

    rm = {}

    if num_samples == 1:
        bot_message = bot_messages[0]
    else:
        print('Bot messages: ', bot_messages)
        print('here')
        bot_message = random.choice(bot_messages)

    return rm, bot_message


def meta_response(turn, call, metaconversation, stage, chat_id, entity):
    phase = get_phase(chat_id)

    if phase == 1:
        if call == 'feelings':
            rm, bot_message, metaconversation, stage = metabot.feelings_conversation(stage, metaconversation, turn, chat_id)
            if metaconversation:
                stage += 1
            else:
                stage = 0
                increment_field(call, chat_id)

        elif call == 'current_situation':
            rm, bot_message, metaconversation, stage = metabot.current_conversation(stage, metaconversation, turn, chat_id)
            if metaconversation:
                stage += 1
            else:
                stage = 0
                increment_field(call, chat_id)

        elif call == 'chatbot_workings':
            rm, bot_message, metaconversation, stage = metabot.workings_conversation(stage, metaconversation, turn, chat_id, entity)
            if metaconversation:
                stage += 1
            else:
                stage = 0
                increment_field(call, chat_id)

    elif phase == 2:
        if call == 'feelings' or call == 'current_situation':
            rm, bot_message, metaconversation, stage = metabot.feelings_phase_2(stage, metaconversation, turn, chat_id, entity)
            if metaconversation:
                stage += 1
            else:
                stage = 0
                increment_field(call, chat_id)

        elif call == 'chatbot_workings':
            rm, bot_message, metaconversation, stage = metabot.workings_conversation(stage, metaconversation, turn, chat_id, entity)
            if metaconversation:
                stage += 1
            else:
                stage = 0
                increment_field(call, chat_id)

    elif phase == 3:
        if call == 'feelings' or call == 'current_situation':
            rm, bot_message, metaconversation, stage = metabot.feelings_phase_3(stage, metaconversation, turn, chat_id, entity)
            if metaconversation:
                stage += 1
            else:
                stage = 0
                increment_field(call, chat_id)

        elif call == 'chatbot_workings':
            rm, bot_message, metaconversation, stage = metabot.workings_conversation(stage, metaconversation, turn, chat_id, entity)
            if metaconversation:
                stage += 1
            else:
                stage = 0
                increment_field(call, chat_id)

    return rm, bot_message, metaconversation, stage


def reply_message(turn, num_samples, model, tokenizer, history, config, mmi_model, 
    mmi_tokenizer, metaconversation, stage, call, entity, chat_id):

    turn  = turn[0]

    call, metaconversation, entity = check_utterance(turn, metaconversation, call, entity)

    if metaconversation:
        rm, bot_message, metaconversation, stage = meta_response(turn, call, metaconversation, stage, chat_id, entity)

    else:
        rm, bot_message = bot_response(num_samples, model, tokenizer, history, config, mmi_model, mmi_tokenizer)

    return rm, bot_message, metaconversation, stage, call, entity


def save_conversation(turn, chat_id, field):
    message_time = datetime.now().strftime("%H:%M:%S")
    message_date = datetime.now().strftime("%Y:%m:%d")
    message_day = calendar.day_name[datetime.today().weekday()]

    complete_message = ' - '.join([message_day, message_date, message_time, turn])

    data = {field: complete_message}

    insert_data(data, chat_id, multiple = True)

