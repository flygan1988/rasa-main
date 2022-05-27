import asyncio
import time
import inspect
from sanic import Sanic, Blueprint, response
from sanic.request import Request
from sanic.response import HTTPResponse
from typing import Text, Dict, Any, Optional, Callable, Awaitable, NoReturn
from rasa_sdk import utils
from rasa.core.channels import (
    InputChannel,
    CollectingOutputChannel,
    UserMessage,
)
# from addons import log_util
from utils.constants import MYSQL_USER, MYSQL_DBNAME, MYSQL_HOST, MYSQL_PASSWORD, MYSQL_PORT
from knowledgebase.car_knowledgebase import CarKnowledgeBase
import logging

logger = logging.getLogger(__name__)

class SaicIO(InputChannel):

    @classmethod
    def name(cls) -> Text:
        return "saicio"

    @classmethod
    def from_credentials(cls, credentials: Optional[Dict[Text, Any]]) -> InputChannel:
        if not credentials:
            cls.raise_missing_credentials_exception()

        return cls(credentials.get("username"),
                   credentials.get("password"),
                   )

    def __init__(self, username, password) -> None:
        self.username = username
        self.password = password
        self.knowledge_base = CarKnowledgeBase(MYSQL_DBNAME, MYSQL_USER, MYSQL_PASSWORD, MYSQL_HOST)

    def blueprint(
            self, on_new_message: Callable[[UserMessage], Awaitable[Any]]
    ) -> Blueprint:
        custom_webhok = Blueprint(
            "custom_webhook_{}".format(type(self).__name__),
            inspect.getmodule(self).__name__,
        )

        @custom_webhok.route("/", methods=["GET"])
        async def health(request: Request) -> HTTPResponse:
            return response.json({"status": "ok"})

        @custom_webhok.route("/webhook", methods=["POST"])
        async def receive(request: Request) -> HTTPResponse:
            sender_id = request.json.get("sender")
            text = request.json.get("message")
            input_channel = self.name()
            metadata = self.get_metadata(request)
            collector = CollectingOutputChannel()

            await on_new_message(
                UserMessage(
                    text,
                    collector,
                    sender_id,
                    input_channel=input_channel,
                    metadata=metadata,
                )
            )

            text = text.replace("\"", "")
            bot_response = str(collector.messages)
            bot_response = bot_response.replace("\"", "")
            print(text)
            print(metadata)
            print(bot_response)
            await self.knowledge_base.insert_conversation_history(sender_id, text, bot_response,
                                                                  str(metadata) if metadata else None, time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))

            # 响应
            return response.json(collector.messages)

        return custom_webhok

    def get_metadata(self, request: Request) -> Optional[Dict[Text, Any]]:
        return request.json.get("metadata", None)
