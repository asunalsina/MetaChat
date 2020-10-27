import pymongo, json, time
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from datetime import datetime, timedelta

from model.conversationDataframe import ConversationDataframe
from stats.iConvStats import IConvStats

with open('tokens.json') as f:
    token_file = json.loads(f.read())

# Create the client and the database
client = pymongo.MongoClient(token_file['mongodb_token'])
db=client.users_database

with open('rulebased/rule_sentences.json') as file:
    sentences = json.loads(file.read())


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
    

def plot_statistics(chat_id, keywords, db = db):

    sentences_dataframe = create_df(chat_id)

    conv = ConversationDataframe(sentences_dataframe)
    conv.loadMessages()
    
    ### BASIC STATS
    basic_stats = conv.stats.generateStats(IConvStats.STATS_NAME_BASICLENGTH)
    basic_user = basic_stats.loc[str(chat_id)]

    basic_hour_stats = conv.stats.generateStatsByHour(IConvStats.STATS_NAME_BASICLENGTH)
    basic_hour_user = basic_hour_stats.loc[str(chat_id)]

    basic_hour_user.plot(y = ['numMsgs', 'avgLen'], kind = 'bar')
    plt.savefig(f'graphs/basic_hour_num{chat_id}.png')
    plt.clf()

    basic_hour_user.plot(y = 'lenMsgs', kind = 'bar')
    plt.savefig(f'graphs/basic_hour_len{chat_id}.png')
    plt.clf()

    basic_datetime_stats = conv.stats.generateStatsByYearMonthDayHour(IConvStats.STATS_NAME_BASICLENGTH)
    basic_datetime_user = basic_datetime_stats.loc[str(chat_id)]
    new_index = [datetime(value[0], value[1], value[2], value[3]) for value in basic_datetime_user.index]
    basic_datetime_user.index = new_index

    basic_datetime_user.plot(y = ['numMsgs', 'avgLen'], kind = 'bar')
    plt.gcf().autofmt_xdate()
    plt.savefig(f'graphs/basic_datetime_num{chat_id}.png')
    plt.clf()

    basic_datetime_user.plot(y = 'lenMsgs', kind = 'bar')
    plt.gcf().autofmt_xdate()
    plt.savefig(f'graphs/basic_datetime_len{chat_id}.png')
    plt.clf()


    ### INTERVALS
    start, end, interval = conv.stats.getIntervalStats()
    days = conv.stats.getDaysWithoutMessages()


    ### LEXICAL STATS
    lexical_stats = conv.stats.generateStats(IConvStats.STATS_NAME_LEXICAL)
    lexical_user = lexical_stats.loc[str(chat_id)]

    lexical_hour_stats = conv.stats.generateStatsByHour(IConvStats.STATS_NAME_LEXICAL)
    lexical_hour_user = lexical_hour_stats.reset_index('sender', drop = True)

    lexical_hour_user.plot(y = ['tokensCount', 'vocabularyCount'], kind = 'bar')
    plt.savefig(f'graphs/lexical_hour_num{chat_id}.png')
    plt.clf()

    lexical_hour_user.plot(y = 'lexicalRichness', kind = 'bar')
    plt.savefig(f'graphs/lexical_hour_len{chat_id}.png')
    plt.clf()

    lexical_datetime_stats = conv.stats.generateStatsByYearMonthDayHour(IConvStats.STATS_NAME_LEXICAL)
    lexical_datetime_user = lexical_datetime_stats.reset_index('sender', drop = True)
    new_index = [datetime(value[0], value[1], value[2], value[3]) for value in lexical_datetime_user.index]
    lexical_datetime_user.index = new_index

    lexical_datetime_user.plot(y = ['tokensCount', 'vocabularyCount'], kind = 'bar')
    plt.gcf().autofmt_xdate()
    plt.savefig(f'graphs/lexical_datetime_num{chat_id}.png')
    plt.clf()
    
    lexical_datetime_user.plot(y = 'lexicalRichness', kind = 'bar')
    plt.gcf().autofmt_xdate()
    plt.savefig(f'graphs/lexical_datetime_len{chat_id}.png')
    plt.clf()


    ### WORD STATS
    word_stats = conv.stats.generateStats(IConvStats.STATS_NAME_WORDCOUNT)
    word_user = word_stats.wordsCount.loc[str(chat_id)]

    word_hour_stats = conv.stats.generateStatsByHour(IConvStats.STATS_NAME_WORDCOUNT)
    word_hour_user = word_hour_stats.wordsCount.reset_index('sender', drop = True)

    word_datetime_stats = conv.stats.generateStatsByYearMonthDayHour(IConvStats.STATS_NAME_WORDCOUNT)
    word_datetime_user = word_datetime_stats.wordsCount.reset_index('sender', drop = True)
    word_datetime_user.index = [datetime(value[0], value[1], value[2], value[3]) for value in word_datetime_user.index]

    word_dict = {}
    word_hour_df = word_datetime_df = pd.DataFrame()

    for key in keywords:
        if key in word_user.index:
            word_dict[key] = word_user[key]
        if key in word_hour_user:
            word_hour_df = pd.concat([word_hour_df, word_hour_user[key]], axis = 1)
        if key in word_datetime_user:
            word_datetime_df = pd.concat([word_datetime_df, word_datetime_user[key]], axis = 1)


    plt.bar(word_dict.keys(), word_dict.values())
    plt.savefig(f'graphs/words{chat_id}.png')
    plt.clf()

    word_hour_df.plot(kind = 'bar')
    plt.gcf().autofmt_xdate()
    plt.savefig(f'graphs/word_hour{chat_id}.png')
    plt.clf()

    word_datetime_df.plot(kind = 'bar')
    plt.gcf().autofmt_xdate()
    plt.savefig(f'graphs/word_datetime{chat_id}.png')
    plt.clf()



if __name__ == '__main__':

    users = db.users.find({})
    keywords = set([b[0].lower() for button in sentences['buttons'] for b in sentences['buttons'][button] if button in ['feelings', 'distress', 'malfunction'] if b[0].lower() not in ['none', 'other', 'too repetitive', 'not clear enough']])

    for user in users:
        data = plot_statistics(user['chat_id'], keywords)