# Metadialogue Chatbot

The meta-dialogue chatbot is based on the [gpt2bot](https://github.com/polakowo/gpt2bot) telegram DialoGPT bot.

The stats are calculated using 5agado's [conversation_analyzer](https://github.com/5agado/conversation-analyzer).

## How to use?

#### Requirements

The requirements can be installed in a [virtual enviroment](https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/#installing-virtualenv). Once the virtual environment is activated, install the required libraries running:

```
$ pip install -r requirements.txt
```

#### Tokens

There are several needed tokens (telegram bot, wit.ai app and mongodb cluster). These tokens need to be writen in **tokens.json** and **/gpt2bot/chatbot.cfg**.
