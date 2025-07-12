import os
from langchain.memory import ConversationBufferMemory
from langchain_community.chat_message_histories import RedisChatMessageHistory
from dotenv import load_dotenv
load_dotenv()

REDIS_URL = os.environ.get("REDIS_URL")

class RedisConversationMemory:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.history = RedisChatMessageHistory(session_id=session_id, url=REDIS_URL)
        self.memory = ConversationBufferMemory(
            chat_memory=self.history,
            return_messages=True,
            memory_key="history"
        )

    def load_memory(self):
        return self.memory

    def clear(self):
        self.history.clear()

    def get_history(self):
        return self.history.messages

    def add_user_message(self, content):
        self.history.add_user_message(content)

    def add_ai_message(self, content):
        self.history.add_ai_message(content) 