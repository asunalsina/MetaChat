import telegram
import json
import requests
import pymongo
import schedule, time, datetime
import numpy as np
from functools import reduce

with open('tokens.json') as f:
    token_file = json.loads(f.read())

with open('rulebased/rule_sentences.json') as file:
    sentences = json.loads(file.read())

token = token_file['telegram_token']

client = pymongo.MongoClient(token_file['mongodb_token'])
db=client.users_database

def telegram_bot_sendtext(chat_id, bot_message):
    bot = telegram.Bot(token=token)
    bot.sendMessage(chat_id=chat_id, text=bot_message)

def reducer(accumulator, element):
    for key, value in element.items():
        accumulator[key] = accumulator.get(key, 0) + value
    return accumulator

def get_hours(keyword, users):
    # Get the hours when the users express negative feelings
    schedule_dict = {}

    for user in users:
        if 'reminders' in user.keys():
            if user['reminders'] == 'daily':
                chat_id = user['chat_id']
                data_dict = user['Stats'][0]['Word'][0]['Hour']
                keyword_dict = [data_dict[key] for key in keywords if key in data_dict.keys()]
                combined_dicts = reduce(reducer, keyword_dict, {})
                selected_hours = [k for k, v in combined_dicts.items() if v > 5]
                schedule_dict[chat_id] = convert_format_hours(selected_hours)

    return schedule_dict

def convert_format_hours(selected_hours):

    return [datetime.time(int(hour)).strftime('%H:%M') for hour in selected_hours]

def schedule_messages(schedule_dict, message):
    for k,v in schedule_dict.items():
        if len(v) == 1:
            schedule.every().day.at(v[0]).do(telegram_bot_sendtext, k, message).tag('daily')
        else:
            task_time = v[np.random.randint(len(v))]
            print(f'Task time: {task_time}')
            schedule.every().day.at(task_time).do(telegram_bot_sendtext, k, message).tag('daily')

def create_schedule(keywords, users, message):
    print('New schedules')
    # Clean the previous schedule
    schedule.clear('daily')
    # Get the new hours and schedule one message per day
    schedule_dict = get_hours(keywords, users)
    schedule_messages(schedule_dict, message)

if __name__ == '__main__':
    message = 'Remember to take a break!'

    users = db.users.find()

    keywords = ['lonely', 'depressed', 'afraid', 'sad', 'stressed', 'overwhelmed']

    schedule.every().day.at('00:00').do(create_schedule, keywords, users, message)

    while True:
        schedule.run_pending()
        time.sleep(1500)

