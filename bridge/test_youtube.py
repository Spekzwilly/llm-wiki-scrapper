"""Tests for extract_youtube_transcript."""
import pytest
from server import extract_youtube_transcript

# A short public video known to have captions (Andrej Karpathy's "The spelled-out intro to neural networks")
CAPTIONED_URL = "https://www.youtube.com/watch?v=VMj-3S1tku0"

# A video ID that does not exist — guaranteed to have no transcript
NONEXISTENT_URL = "https://www.youtube.com/watch?v=XXXXXXXXXXX"


def test_returns_nonempty_string_for_captioned_video():
    text = extract_youtube_transcript(CAPTIONED_URL)
    assert isinstance(text, str)
    assert len(text) > 100


def test_no_timestamps_in_output():
    text = extract_youtube_transcript(CAPTIONED_URL)
    # Timestamps look like "[0:00]" or "0:00" — neither should appear as standalone tokens
    assert "[0:00]" not in text


def test_raises_for_missing_transcript():
    with pytest.raises(Exception):
        extract_youtube_transcript(NONEXISTENT_URL)


def test_raises_for_unparseable_url():
    with pytest.raises(ValueError, match="Could not parse video ID"):
        extract_youtube_transcript("https://youtube.com/")
