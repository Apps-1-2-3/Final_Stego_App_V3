"""
StegoVault V4

Video Decoder

Handles complete decoding pipeline.
"""

import os
import random
from PIL import Image

from .ffmpeg_utils import (
    create_workspace,
    cleanup_workspace,
    extract_frames,
)

from .frame_manager import (
    load_frame,
)

from .frame_selector import (
    frame_score,
    password_seed,
)

from .chunk_manager import (
    parse_header,
    merge_packets,
    verify_packets,
)

from ..extraction import extract
from ..encryption import decrypt


class VideoDecoder:

    def __init__(self):
        self.workspace = None
        self.frames = []

    def prepare(self, video_path):
        """Create workspace and extract video frames."""
        self.workspace = create_workspace()
        self.frames = extract_frames(video_path, self.workspace)

    def decode(self, password):
        """
        Extract and decrypt message using complexity-based frame selection.
        Optimized to calculate frame scores once and guess total packet counts.
        """
        if not self.frames:
            raise Exception("No frames extracted from the video.")

        # 1. Score all frames once for complexity
        scored = []
        for index, path in enumerate(self.frames):
            img = load_frame(path)
            score = frame_score(img)
            scored.append((index, score["score"]))

        # Sort scored frames descending by complexity
        scored.sort(key=lambda x: x[1], reverse=True)

        correct_chosen = None
        correct_total = None

        # The maximum possible packet count is the number of frames
        max_guess = len(self.frames)

        # 2. Iterate to guess the packet count
        for guess in range(1, max_guess + 1):
            # Replicate the candidate selection inside choose_frames
            candidates = scored[:max(guess * 3, guess)]

            # Shuffle candidates deterministically based on password seed
            candidates_copy = list(candidates)
            rng = random.Random(password_seed(password))
            rng.shuffle(candidates_copy)

            # Select the chosen indices and sort them chronologically
            chosen = sorted([x[0] for x in candidates_copy[:guess]])

            # Load the first chronological frame in chosen list
            first_idx = chosen[0]
            first_frame_path = self.frames[first_idx]
            img = load_frame(first_frame_path)

            try:
                packet = extract(img, password)
                info = parse_header(packet)
                if info["total"] == guess:
                    correct_chosen = chosen
                    correct_total = guess
                    break
            except Exception:
                continue

        if correct_chosen is None:
            raise Exception(
                "Failed to locate steganographic packets. "
                "Wrong password or video does not contain a StegoVault payload."
            )

        # 3. Extract packets from all selected frames
        packets = []
        for idx in correct_chosen:
            frame_path = self.frames[idx]
            img = load_frame(frame_path)
            packet = extract(img, password)
            packets.append(packet)

        # 4. Verify packet integrity and merge
        verify_packets(packets)
        ciphertext = merge_packets(packets)

        # 5. Decrypt the payload
        message = decrypt(ciphertext, password)
        return message

    def cleanup(self):
        """Clean up temporary workspace."""
        if self.workspace:
            cleanup_workspace(self.workspace)
