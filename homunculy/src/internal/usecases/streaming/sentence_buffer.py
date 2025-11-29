"""
Sentence Buffer - Accumulate text and extract complete sentences.

Single Responsibility: Buffer streaming text and yield complete sentences.
This is a domain utility used by streaming use cases.
"""

from typing import Optional


SENTENCE_DELIMITERS = frozenset({".", "!", "?", "。", "！", "？", "\n"})


class SentenceBuffer:
    """Buffer that accumulates text and yields complete sentences."""

    def __init__(self) -> None:
        """Initialize empty buffer."""
        self._buffer = ""

    def add(self, text: str) -> None:
        """Add text to the buffer."""
        self._buffer += text

    def extract_sentence(self) -> Optional[str]:
        """Extract one complete sentence from buffer, if available."""
        delimiter_pos = self._find_last_delimiter()

        if delimiter_pos < 0:
            return None

        sentence = self._buffer[: delimiter_pos + 1].strip()
        self._buffer = self._buffer[delimiter_pos + 1 :]

        return sentence if sentence else None

    def flush(self) -> Optional[str]:
        """Flush remaining buffer content."""
        remaining = self._buffer.strip()
        self._buffer = ""
        return remaining if remaining else None

    def _find_last_delimiter(self) -> int:
        """Find position of last sentence delimiter."""
        last_pos = -1
        for delim in SENTENCE_DELIMITERS:
            pos = self._buffer.rfind(delim)
            if pos > last_pos:
                last_pos = pos
        return last_pos


def create_sentence_buffer() -> SentenceBuffer:
    """Factory function for creating sentence buffer."""
    return SentenceBuffer()
