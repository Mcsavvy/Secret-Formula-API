from typing import Any, Dict, Iterator, List, Optional, Type, Union

from langchain.callbacks.base import Callbacks
from langchain.callbacks.manager import CallbackManagerForLLMRun
from langchain.chains import ConversationChain
from langchain.chat_models import FakeListChatModel
from langchain.chat_models.base import BaseChatModel, BaseMessage
from langchain.schema.output import ChatGenerationChunk, ChatResult
from langchain.schema.prompt_template import BasePromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import Field, root_validator

from cookgpt import logging
from cookgpt.chatbot.data.fake_data import responses
from cookgpt.chatbot.data.prompts import prompt as PROMPT
from cookgpt.chatbot.memory import BaseMemory, ThreadMemory
from cookgpt.ext.config import config
from cookgpt.globals import getvar, setvar


def get_llm() -> BaseChatModel:  # pragma: no cover
    """returns the language model"""
    llm_cls: Type[LLM | FakeLLM]
    if config.USE_GEMINI:
        llm_cls = LLM
    else:
        llm_cls = FakeLLM
    return llm_cls(streaming=config.LLM_STREAMING)  # type: ignore[return-value]


def get_chain_input_key() -> str:
    """returns the input key for the chain"""
    return config.CHATBOT_CHAIN_INPUT_KEY


class FakeLLM(FakeListChatModel):
    """fake language model for testing purposes"""

    streaming: bool
    responses: List = responses
    i: int = 0

    def _stream(
        self,
        messages: List[BaseMessage],
        stop: Union[List[str], None] = None,
        run_manager: Union[CallbackManagerForLLMRun, None] = None,
        **kwargs: Any,
    ) -> Iterator[ChatGenerationChunk]:
        for c in super()._stream(messages, stop, run_manager, **kwargs):
            yield c
            if run_manager:
                run_manager.on_llm_new_token(c.message.content)

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: List[str] | None = None,
        run_manager: CallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> ChatResult:
        if self.streaming:
            logging.debug("Streaming FakeLLM...")
            generation: Optional[ChatGenerationChunk] = None
            for chunk in self._stream(messages, stop, run_manager, **kwargs):
                if generation is None:
                    generation = chunk
                else:
                    generation += chunk
            assert generation is not None
            return ChatResult(generations=[generation])
        else:  # pragma: no cover
            logging.debug("Generating FakeLLM...")
            return super()._generate(messages, stop, run_manager, **kwargs)


class LLM(ChatGoogleGenerativeAI):
    """language model for the chatbot"""

    ...


class ThreadChain(ConversationChain):
    """custom chain for the language model"""

    input_key: str = Field(default_factory=get_chain_input_key)
    llm: "BaseChatModel" = Field(default_factory=get_llm)
    prompt: "BasePromptTemplate" = PROMPT
    memory: "BaseMemory" = Field(default_factory=ThreadMemory)

    @root_validator
    def set_context(cls, values):
        """set context"""
        setvar("memory", values["memory"])
        return values

    def reload(self):  # pragma: no cover
        """reload variables"""
        self.input_key = get_chain_input_key()
        self.llm = get_llm()

    def __call__(
        self,
        inputs: Dict[str, Any] | Any,
        return_only_outputs: bool = False,
        callbacks: Callbacks = None,
        *,
        tags: List[str] | None = None,
        metadata: Dict[str, Any] | None = None,
        include_run_info: bool = False,
    ) -> Dict[str, Any]:
        from langchain.schema import HumanMessage

        from cookgpt.chatbot.models import Chat

        # ensure that the input key is provided
        assert config.CHATBOT_CHAIN_INPUT_KEY in inputs, (
            "Please provide a value for the input key "
            f"({config.CHATBOT_CHAIN_INPUT_KEY})."
        )

        input: str = inputs[config.CHATBOT_CHAIN_INPUT_KEY]
        msg = HumanMessage(content=input)
        # set the id of the query
        if (query := getvar("query", Chat, None)) is not None:
            msg.additional_kwargs["id"] = query.pk
        inputs[config.CHATBOT_CHAIN_INPUT_KEY] = [msg]

        return super().__call__(
            inputs,
            return_only_outputs,
            callbacks,
            tags=tags,
            metadata=metadata,
            include_run_info=include_run_info,
        )

    @property
    def _chain_type(self) -> str:  # pragma: no cover
        return "thread_chain"
