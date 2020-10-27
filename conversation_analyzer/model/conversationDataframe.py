import logging
import time

import util.io as mio
from model.iConversation import IConversation
from model.message import Message
from stats.convStatsDataframe import ConvStatsDataframe


class ConversationDataframe(IConversation):
    def __init__(self, filepath):
        super().__init__(filepath)

    def loadMessages(self, limit=0, startDate=None, endDate=None):
        self.senders = self.filepath['sender']
        self.messages = self.filepath

        self.stats = ConvStatsDataframe(self)
