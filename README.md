# Metadialogue Chatbot

The meta-dialogue chatbot is based on the [gpt2bot](https://github.com/polakowo/gpt2bot) telegram DialoGPT bot.

## How to use?

#### Clone the repository

```
$ git clone https://github.com/asunalsina/MetaChat.git
$ cd MetaChat
```

#### Install the requirements

The requirements can be installed in a [virtual enviroment](https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/#installing-virtualenv). Once the virtual environment is activated, install the required libraries running:

```
$ pip install -r requirements.txt
```

#### Tokens

There are several tokens needed (telegram bot, wit.ai app and mongodb cluster). These tokens need to be writen in **tokens.json** and **/gpt2bot/chatbot.cfg**.

1. Register a new Telegram bot via [BotFather](https://core.telegram.org/bots)
2. Register in [Wit.ai](https://wit.ai/docs/quickstart)
3. Register in [MongoDB Atlas](https://docs.atlas.mongodb.com/getting-started/)

#### Run the chatbot

```
$ python /gpt2bot/telegram_bot.py
```

