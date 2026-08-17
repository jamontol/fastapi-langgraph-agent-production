"""Unit tests for app.utils.graph."""

from langchain_core.messages import AIMessage

from app.schemas.chat import Message
from app.utils.graph import dump_messages, extract_text_content, process_llm_response


class TestExtractTextContent:
    """Tests for extract_text_content."""

    def test_plain_string_passthrough(self):
        """A plain string is returned unchanged."""
        assert extract_text_content("hello") == "hello"

    def test_empty_string(self):
        """An empty string is returned as-is."""
        assert extract_text_content("") == ""

    def test_string_blocks(self):
        """String blocks are concatenated."""
        assert extract_text_content(["a", "b"]) == "ab"

    def test_text_blocks_only(self):
        """Only text blocks contribute to the result."""
        content = [
            {"type": "reasoning", "id": "r1", "summary": []},
            {"type": "text", "text": "answer"},
        ]
        assert extract_text_content(content) == "answer"

    def test_no_extractable_blocks(self):
        """Blocks without text yield an empty string."""
        assert extract_text_content([{"type": "reasoning", "text": "hidden"}]) == ""


class TestDumpMessages:
    """Tests for dump_messages."""

    def test_dumps_to_dicts(self):
        """Messages are dumped to plain dicts."""
        messages = [Message(role="user", content="hi"), Message(role="assistant", content="hello")]
        dumped = dump_messages(messages)
        assert dumped == [{"role": "user", "content": "hi"}, {"role": "assistant", "content": "hello"}]

    def test_empty_list(self):
        """An empty list returns an empty list."""
        assert dump_messages([]) == []


class TestProcessLlmResponse:
    """Tests for process_llm_response."""

    def test_unwraps_structured_content(self):
        """Structured content blocks are collapsed to plain text."""
        response = AIMessage(content=[{"type": "text", "text": "answer"}])
        assert process_llm_response(response).content == "answer"

    def test_leaves_plain_string(self):
        """Plain string content is left unchanged."""
        response = AIMessage(content="answer")
        assert process_llm_response(response).content == "answer"
