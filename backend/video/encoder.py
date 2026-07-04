"""
StegoVault V4

Video Encoder

Handles complete encoding pipeline.
"""

import os
import shutil

from PIL import Image

from .ffmpeg_utils import (
    create_workspace,
    cleanup_workspace,
    extract_frames,
    extract_audio,
    build_video,
    merge_audio,
)

from .frame_manager import (
    get_video_info,
    load_frame,
    save_frame,
    validate_payload,
)

from .frame_selector import (
    choose_frames,
)

from .chunk_manager import (
    split_ciphertext,
)

from ..encryption import encrypt
from ..embedding import embed


class VideoEncoder:

    def __init__(self):

        self.workspace = None

        self.video_info = None

        self.frames = []

        self.audio = None

        self.selected_frames = []

        self.ciphertext = b""

        self.packets = []



    def prepare(self, video_path):

        self.workspace = create_workspace()

        self.video_info = get_video_info(video_path)

        self.frames = extract_frames(

            video_path,

            self.workspace

        )

        self.audio = extract_audio(

            video_path,

            self.workspace

        )



    def encrypt_message(

        self,

        message,

        password

    ):

        self.ciphertext = encrypt(

            message,

            password

        )



    def split_payload(self):

        self.packets = split_ciphertext(

            self.ciphertext,

            max(

                1,

                len(self.frames)//25

            )

        )



    def choose_embedding_frames(
        self,
        password
    ):
        self.selected_frames = choose_frames(
            self.frames,
            password,
            len(self.packets)
        )

    def encode(self, password, output_path=None):
        """Embed packets, compile video, and return bytes or copy to output_path."""
        for frame_number, packet in zip(self.selected_frames, self.packets):
            frame_path = self.frames[frame_number]
            img = load_frame(frame_path)
            stego = embed(img, packet, password)
            save_frame(stego, frame_path)

        # Build video from modified frames
        temp_video = build_video(self.workspace, self.video_info["fps"])

        # Merge original audio back
        final_video = merge_audio(temp_video, self.audio, self.workspace)

        if output_path:
            shutil.copyfile(final_video, output_path)
            return output_path

        with open(final_video, "rb") as f:
            video_data = f.read()

        return video_data

    def cleanup(self):
        """Clean up temporary workspace."""
        if self.workspace:
            cleanup_workspace(self.workspace)

        