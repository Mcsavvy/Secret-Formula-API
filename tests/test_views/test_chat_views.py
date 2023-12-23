from time import sleep
from typing import cast
from uuid import uuid4

from flask import url_for
from flask.testing import FlaskClient

from cookgpt.app import App
from cookgpt.chatbot.data.enums import MessageType
from cookgpt.chatbot.models import Chat, Thread
from cookgpt.chatbot.utils import get_thread
from tests.utils import Random


class TestChatsView:
    """Test the thread view"""

    def test_get_all_chats_in_thread(
        self,
        client: "FlaskClient",
        access_token: str,
        query: "Chat",
        thread: Thread,
    ):
        """Test that a user can get all the chats in a thread"""
        headers = {"Authorization": f"Bearer {access_token}"}
        response = client.get(
            url_for("chatbot.all_chats", thread_id=thread.id),
            headers=headers,
        )

        assert response.status_code == 200
        assert response.json is not None
        assert "chats" in response.json
        assert len(response.json["chats"]) == 1

        chat = response.json["chats"][0]
        assert chat["id"] == str(query.id)
        assert chat["content"] == query.content
        assert chat["chat_type"] == "QUERY"
        assert chat["thread_id"] == str(query.thread_id)
        assert chat["cost"] == query.cost
        assert chat["previous_chat_id"] is None
        assert chat["next_chat_id"] is None

    def test_delete_all_chats_in_thread(
        self, client: "FlaskClient", access_token: str, thread: "Thread"
    ):
        """Test that a user can delete all chats in a thread"""
        for i in range(2):
            Random.chat(thread_id=thread.id, order=i)

        assert len(cast(list[Chat], thread.chats)) == 2
        headers = {"Authorization": f"Bearer {access_token}"}
        response = client.delete(
            url_for("chatbot.all_chats"),
            headers=headers,
            json={"thread_id": str(thread.id)},
        )

        assert response.status_code == 200
        assert "message" in response.json  # type: ignore
        assert "deleted" in response.json["message"].lower()  # type: ignore
        assert len(cast(list[Chat], thread.chats)) == 0


class TestChatView:
    """Test the chat view"""

    def test_get_chat(
        self, client: "FlaskClient", access_token: str, query: "Chat"
    ):
        """test get a chat"""
        headers = {"Authorization": f"Bearer {access_token}"}
        response = client.get(
            url_for("chatbot.single_chat", chat_id=query.id), headers=headers
        )

        assert response.status_code == 200
        assert response.json is not None
        chat = response.json

        assert chat["id"] == str(query.id)
        assert chat["content"] == query.content
        assert chat["chat_type"] == "QUERY"
        assert chat["thread_id"] == str(query.thread_id)
        assert chat["cost"] == query.cost
        assert chat["previous_chat_id"] is None
        assert chat["next_chat_id"] is None

    def test_get_non_existent_chat(
        self, client: "FlaskClient", access_token: str
    ):
        """test get a chat that does not exist"""
        headers = {"Authorization": f"Bearer {access_token}"}
        response = client.get(
            url_for("chatbot.single_chat", chat_id=uuid4()), headers=headers
        )

        assert response.status_code == 404
        assert response.json is not None
        assert "message" in response.json
        assert "not found" in response.json["message"].lower()

    def test_delete_chat(
        self,
        client: "FlaskClient",
        access_token: str,
        thread: "Thread",
    ):
        """test delete a chat"""
        query = Random.chat(thread_id=thread.id, order=0)
        headers = {"Authorization": f"Bearer {access_token}"}
        response = client.delete(
            url_for("chatbot.single_chat", chat_id=query.id), headers=headers
        )

        assert response.status_code == 200
        assert response.json is not None
        assert "message" in response.json
        assert "deleted" in response.json["message"].lower()

    def test_delete_non_existent_chat(
        self, client: "FlaskClient", access_token
    ):
        """test delete a chat that does not exist"""
        headers = {"Authorization": f"Bearer {access_token}"}
        response = client.delete(
            url_for("chatbot.single_chat", chat_id=uuid4()), headers=headers
        )

        assert response.status_code == 404
        assert response.json is not None
        assert "message" in response.json
        assert "not found" in response.json["message"].lower()

    def test_send_query(
        self, client: "FlaskClient", access_token: str, thread: "Thread"
    ):
        """Send a query to the chatbot"""
        headers = {"Authorization": f"Bearer {access_token}"}
        data = {"query": "test query", "thread_id": str(thread.id)}
        response = client.post(
            url_for("chatbot.query", stream=False), headers=headers, json=data
        )

        assert response.status_code == 201
        assert response.json is not None

        chat = response.json["chat"]
        streaming = response.json["streaming"]

        for key in [
            "id",
            "content",
            "chat_type",
            "cost",
            "previous_chat_id",
            "next_chat_id",
            "sent_time",
            "thread_id",
        ]:
            assert key in chat, f"{key} not in response"

        assert chat["content"]
        assert chat["chat_type"] == "RESPONSE"
        assert streaming is False

        chats = cast(list[Chat], thread.chats)

        assert len(chats) == 2
        assert chats[0].content == "test query"
        assert chats[0].chat_type == MessageType.QUERY
        assert chats[0].thread_id == thread.id
        assert chats[0].previous_chat_id is None
        assert chats[0].next_chat_id == chats[1].id
        assert chats[1].previous_chat_id == chats[0].id
        assert chats[1].next_chat_id is None
        assert chats[1].thread_id == thread.id
        assert chats[1].chat_type == MessageType.RESPONSE

    def test_send_query__non_existent_thread(
        self, client: "FlaskClient", auth_header: dict
    ):
        """Send query to chatbot using a non-existent thread"""
        data = {"query": "test query", "thread_id": uuid4()}
        response = client.post(
            url_for("chatbot.query", stream=False),
            headers=auth_header,
            json=data,
        )

        assert response.status_code == 404
        assert response.json is not None
        assert "message" in response.json
        assert "not found" in response.json["message"].lower()

    def test_send_query__no_thread_id(
        self, client: "FlaskClient", auth_header: dict
    ):
        """Test implicit thread creation"""
        data = {"query": "test query"}
        response = client.post(
            url_for("chatbot.query", stream=False),
            headers=auth_header,
            json=data,
        )

        assert response.status_code == 201
        assert response.json is not None
        thread = get_thread(response.json["chat"]["thread_id"])

        assert thread.chat_count == 2
        assert cast(list[Chat], thread.chats)[0].content == "test query"

    def test_send_query_existing_chats(
        self,
        client: "FlaskClient",
        auth_header: dict[str, str],
        thread: "Thread",
    ):
        """Test sending a query when there are existing chats in the thread"""
        data = {"query": "I'm great, you?", "thread_id": str(thread.id)}
        thread.add_query("Hi")
        thread.add_response("How are you?")
        client.post(
            url_for("chatbot.query", stream=False),
            headers=auth_header,
            json=data,
        )
        data = {"query": "Alright", "thread_id": str(thread.id)}
        response = client.post(
            url_for("chatbot.query", stream=False),
            headers=auth_header,
            json=data,
        )
        assert response.status_code == 201
        assert response.json is not None
        thread = get_thread(response.json["chat"]["thread_id"])
        assert thread.chat_count == 6

    def test_send_query__streaming(
        self,
        client: "FlaskClient",
        access_token: str,
        thread: "Thread",
    ):
        """Send a query to the chatbot"""
        headers = {"Authorization": f"Bearer {access_token}"}
        data = {"query": "test query", "thread_id": str(thread.id)}
        response = client.post(
            url_for("chatbot.query", stream=True),
            headers=headers,
            json=data,
        )

        assert response.status_code == 201
        assert response.json is not None

        chat = response.json["chat"]
        streaming = response.json["streaming"]

        for key in [
            "id",
            "content",
            "chat_type",
            "cost",
            "previous_chat_id",
            "next_chat_id",
            "sent_time",
            "thread_id",
        ]:
            assert key in chat, f"{key} not in response"

        assert chat["content"] == ""
        assert chat["chat_type"] == "RESPONSE"
        assert streaming is True

        chats = cast(list[Chat], thread.chats)

        assert len(chats) == 2
        assert (
            chats[0].content == ""
        )  # content is empty because it is streaming
        assert chats[0].chat_type == MessageType.QUERY
        assert chats[0].thread_id == thread.id
        assert chats[0].previous_chat_id is None
        assert chats[0].next_chat_id == chats[1].id
        assert chats[1].previous_chat_id == chats[0].id
        assert chats[1].next_chat_id is None
        assert chats[1].thread_id == thread.id
        assert chats[1].chat_type == MessageType.RESPONSE

    def test_send_query_exceeded_max_chat_cost(
        self, client: "FlaskClient", access_token: str, thread: "Thread"
    ):
        """
        Test that a user gets dummy response when they
        exceed max chat cost
        """
        thread.user.update(max_chat_cost=0)
        headers = {"Authorization": f"Bearer {access_token}"}
        data = {"query": "test query", "thread_id": str(thread.id)}
        response = client.post(
            url_for("chatbot.query"), headers=headers, json=data
        )
        assert response.status_code == 200
        assert response.json is not None

        chat = response.json["chat"]
        streaming = response.json["streaming"]

        for key in [
            "id",
            "content",
            "chat_type",
            "cost",
            "previous_chat_id",
            "next_chat_id",
            "sent_time",
            "thread_id",
        ]:
            assert key in chat, f"{key} not in response"

        assert chat["content"]
        assert len(cast(list[Chat], thread.chats)) == 0
        assert chat["chat_type"] == "RESPONSE"
        assert chat["cost"] == 0
        assert chat["thread_id"] == str(thread.id)
        assert chat["previous_chat_id"] is None
        assert chat["next_chat_id"] is None
        assert streaming is False

    def test_send_query_exceeded_max_chat_cost__streaming(
        self, client: "FlaskClient", access_token: str, thread: "Thread"
    ):
        """
        Test that a user gets dummy response when they
        exceed max chat cost while streaming
        """
        thread.user.update(max_chat_cost=0)
        headers = {"Authorization": f"Bearer {access_token}"}
        data = {"query": "test query", "thread_id": str(thread.id)}
        response = client.post(
            url_for("chatbot.query"), headers=headers, json=data
        )
        assert response.status_code == 200
        assert response.json is not None

        chat = response.json["chat"]
        streaming = response.json["streaming"]

        for key in [
            "id",
            "content",
            "chat_type",
            "cost",
            "previous_chat_id",
            "next_chat_id",
            "sent_time",
            "thread_id",
        ]:
            assert key in chat, f"{key} not in response"

        assert chat["chat_type"] == "RESPONSE"
        assert len(cast(list[Chat], thread.chats)) == 0
        assert chat["cost"] == 0
        assert chat["thread_id"] == str(thread.id)
        assert chat["previous_chat_id"] is None
        assert chat["next_chat_id"] is None
        assert streaming is False

    def test_read_stream(
        self, access_token: str, thread: "Thread", client: "FlaskClient"
    ):
        """
        Test that a user can read a chat as a stream
        when the chat was sent as a stream
        """
        query = Random.chat(
            thread_id=thread.id, order=0, chat_type=MessageType.QUERY
        )
        response = client.get(
            url_for("chatbot.read_stream", chat_id=query.id),
            headers={"Authorization": f"Bearer {access_token}"},
        )
        content_bytes = b""
        assert response.status_code == 200

        for token in response.response:
            content_bytes += cast(bytes, token)
        content = content_bytes.decode()
        assert content == query.content

    def test_read_stream__non_existent_chat(
        self, access_token: str, client: "FlaskClient"
    ):
        """
        Test that a user gets 404 when they try to read
        a stream that does not exist
        """
        from uuid import uuid4

        response = client.get(
            url_for("chatbot.read_stream", chat_id=uuid4()),
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 404

    def test_read_stream__streaming_chat(
        self,
        access_token: str,
        app: "App",
        thread: "Thread",
        client: "FlaskClient",
        celery_worker,
    ):
        """
        Test that a when a user sends a query in streaming mode,
        they can read the response as it comes in
        """

        from cookgpt.chatbot.utils import get_stream_name

        client.post(
            url_for("chatbot.query", stream=True),
            headers={"Authorization": f"Bearer {access_token}"},
            json={"query": "test query", "thread_id": str(thread.id)},
        )

        chat = thread.last_chat
        stream = get_stream_name(thread.user, chat)
        task_id = app.redis.get(f"{stream}:task")

        assert task_id, f"Task id for stream {stream!r} not found in redis"
        sleep(10)

        response = client.get(
            url_for("chatbot.read_stream", chat_id=chat.id),
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == 200
        content_bytes = b""

        for token in response.response:
            content_bytes += cast(bytes, token)
        content = content_bytes.decode()
        print(f"content: {content}")
        assert content


class TestChatStreaming:
    """Test the chat streaming view"""
