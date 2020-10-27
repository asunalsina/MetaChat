import pymongo, json, time
import pandas as pd
import numpy as np

from datetime import datetime, timedelta

from model.conversationDataframe import ConversationDataframe
from stats.iConvStats import IConvStats

with open('tokens.json') as f:
    token_file = json.loads(f.read())

# Create the client and the database
client = pymongo.MongoClient(token_file['mongodb_token'])
db=client.users_database


def create_df(chat_id, db = db):
    user = db.users.find_one({'chat_id': chat_id})
    # Prepare the user utterances
    # Each utterance is a list of 4 elements
    # 0: day of the week / 1: date / 2: time / 3: text
    user_utterances = [sentence.split(' - ') for sentence in user['user']]
    
    sender = str(chat_id)

    data = {'year': [], 'month': [], 'day': [], 'date': [], 'hour': [], 'time': [], 
    'datetime': [], 'sender': sender, 'text': []}


    for utterance in user_utterances:
        data['year'].append(int(utterance[1].split(':')[0]))
        data['month'].append(int(utterance[1].split(':')[1]))
        data['day'].append(int(utterance[1].split(':')[2]))
        data['date'].append(datetime.strptime(utterance[1].replace(':', '-'), '%Y-%m-%d'))
        data['hour'].append(int(utterance[2].split(':')[0]))
        data['time'].append(time.strptime(utterance[2], '%H:%M:%S'))
        data['datetime'].append(datetime.strptime((utterance[1].replace(':', '-') + ' ' + utterance[2]), '%Y-%m-%d %H:%M:%S'))
        data['text'].append(utterance[3])

    df = pd.DataFrame(data)

    return df
    

def save_statistics(chat_id, db = db):

    sentences_dataframe = create_df(chat_id)

    conv = ConversationDataframe(sentences_dataframe)
    conv.loadMessages()

    ### BASIC STATS
    basic_stats = conv.stats.generateStats(IConvStats.STATS_NAME_BASICLENGTH)
    basic_user = basic_stats.loc[str(chat_id)].to_dict()

    basic_hour_stats = conv.stats.generateStatsByHour(IConvStats.STATS_NAME_BASICLENGTH)
    # Convert the index to string
    basic_hour_user = basic_hour_stats.loc[str(chat_id)]
    basic_hour_user.index = basic_hour_user.index.map(str)
    basic_hour_user = basic_hour_user.to_dict()

    basic_datetime_stats = conv.stats.generateStatsByYearMonthDayHour(IConvStats.STATS_NAME_BASICLENGTH)
    # Conver the index to string
    basic_datetime_user = basic_datetime_stats.loc[str(chat_id)]
    basic_datetime_user.index = [datetime(value[0], value[1], value[2], value[3]) for value in basic_datetime_user.index]
    basic_datetime_user.index = basic_datetime_user.index.map(str)
    basic_datetime_user = basic_datetime_user.to_dict()


    ### INTERVALS
    start, end, interval = conv.stats.getIntervalStats()
    days = conv.stats.getDaysWithoutMessages()


    ### LEXICAL STATS
    lexical_stats = conv.stats.generateStats(IConvStats.STATS_NAME_LEXICAL)
    lexical_user = lexical_stats.loc[str(chat_id)].to_dict()

    lexical_hour_stats = conv.stats.generateStatsByHour(IConvStats.STATS_NAME_LEXICAL)
    # Convert the index to string
    lexical_hour_user = lexical_hour_stats.reset_index('sender', drop = True)
    lexical_hour_user.index = lexical_hour_user.index.map(str)
    lexical_hour_user = lexical_hour_user.to_dict()

    lexical_datetime_stats = conv.stats.generateStatsByYearMonthDayHour(IConvStats.STATS_NAME_LEXICAL)
    # Conver the index to string
    lexical_datetime_user = lexical_datetime_stats.reset_index('sender', drop = True)
    lexical_datetime_user.index = [datetime(value[0], value[1], value[2], value[3]) for value in lexical_datetime_user.index]
    lexical_datetime_user.index = lexical_datetime_user.index.map(str)
    lexical_datetime_user = lexical_datetime_user.to_dict()


    ### WORD STATS
    word_stats = conv.stats.generateStats(IConvStats.STATS_NAME_WORDCOUNT)
    word_user = word_stats.wordsCount.loc[str(chat_id)].to_dict()

    word_hour_stats = conv.stats.generateStatsByHour(IConvStats.STATS_NAME_WORDCOUNT)
    # Convert the index to string
    word_hour_user = word_hour_stats.wordsCount.reset_index('sender', drop = True)
    word_hour_user.index = word_hour_user.index.map(str)
    word_hour_user = word_hour_user.to_dict()

    word_datetime_stats = conv.stats.generateStatsByYearMonthDayHour(IConvStats.STATS_NAME_WORDCOUNT)
    # Convert the index to string
    word_datetime_user = word_datetime_stats.wordsCount.reset_index('sender', drop = True)
    word_datetime_user.index = [datetime(value[0], value[1], value[2], value[3]) for value in word_datetime_user.index]
    word_datetime_user.index = word_datetime_user.index.map(str)
    word_datetime_user = word_datetime_user.to_dict()


    ### EMOTICONS STATS
    emoticon_stats = conv.stats.generateStats(IConvStats.STATS_NAME_EMOTICONS)
    emoticon_user = emoticon_stats.loc[str(chat_id)].to_dict()


    # UPDATE DATA
    data = {'Stats': [{'Basic': [{'Total': basic_user, 'Hour': basic_hour_user, 'Datetime': basic_datetime_user}],
    'Interval_data': [{'Start': start.to_pydatetime(), 'End': end.to_pydatetime(), 'Interval': interval.total_seconds(), 'Days': list(days)}], 
    'Lexical': [{'Total': lexical_user, 'Hour': lexical_hour_user, 'Datetime': lexical_datetime_user}], 
    'Word': [{'Total': word_user, 'Hour': word_hour_user, 'Datetime': word_datetime_user}], 
    'Emoticon': emoticon_user}]}


    db.users.update_one({'chat_id': chat_id}, {'$set': data})


if __name__ == '__main__':

    users = db.users.find({})

    for user in users:
        save_statistics(user['chat_id'])

