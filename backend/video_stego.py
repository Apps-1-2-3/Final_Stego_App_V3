"""
Bridge module mapping video steganography API calls to the
StegoVault V4 VideoEncoder and VideoDecoder modular engines.
"""

from .video.encoder import VideoEncoder
from .video.decoder import VideoDecoder


def embed_message_in_video(
    video_path: str,
    message: str,
    password: str,
    output_path: str | None = None,
) -> bytes:
    """
    Encode an encrypted message across multiple video frames using
    adaptive complexity-based frame selection and audio preservation.
    """
    encoder = VideoEncoder()
    try:
        encoder.prepare(video_path)
        encoder.encrypt_message(message, password)
        encoder.split_payload()
        encoder.choose_embedding_frames(password)
        return encoder.encode(password, output_path=output_path)
    finally:
        encoder.cleanup()


def extract_message_from_video(video_path: str, password: str) -> str:
    """
    Extract and decrypt a message hidden inside a stego video file
    using adaptive complexity-based decoding.
    """
    decoder = VideoDecoder()
    try:
        decoder.prepare(video_path)
        return decoder.decode(password)
    finally:
        decoder.cleanup()
