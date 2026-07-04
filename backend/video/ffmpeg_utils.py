"""
StegoVault Video Steganography
FFmpeg Utility Functions

Responsible for:
- Checking FFmpeg installation
- Extracting frames
- Extracting audio
- Rebuilding videos
- Combining video + audio
"""

import os
import shutil
import subprocess
import tempfile


# ----------------------------------------------------------
# FFMPEG CHECK
# ----------------------------------------------------------

def check_ffmpeg():
    """
    Verify FFmpeg is installed.
    """
    try:

        subprocess.run(
            ["ffmpeg", "-version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True
        )

        return True

    except Exception:
        return False

# ----------------------------------------------------------
# WORKSPACE
# ----------------------------------------------------------

def create_workspace():

    workspace = tempfile.mkdtemp(prefix="stegovideo_")

    frames = os.path.join(workspace, "frames")
    audio = os.path.join(workspace, "audio")
    output = os.path.join(workspace, "output")

    os.makedirs(frames, exist_ok=True)
    os.makedirs(audio, exist_ok=True)
    os.makedirs(output, exist_ok=True)

    return {
        "root": workspace,
        "frames": frames,
        "audio": audio,
        "output": output
    }


def cleanup_workspace(workspace):

    if os.path.exists(workspace["root"]):
        shutil.rmtree(
            workspace["root"],
            ignore_errors=True
        )


# ----------------------------------------------------------
# EXTRACT VIDEO FRAMES
# ----------------------------------------------------------

def extract_frames(video_path, workspace):

    frame_pattern = os.path.join(
        workspace["frames"],
        "frame_%06d.png"
    )

    cmd = [
        "ffmpeg",
        "-y",
        "-i",

        video_path,
        frame_pattern
    ]

    process = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    if process.returncode != 0:
        raise Exception(process.stderr)

    frames = sorted([
        os.path.join(
            workspace["frames"],
            f

        )

        for f in os.listdir(workspace["frames"])

        if f.endswith(".png")

    ])

    if len(frames) == 0:

        raise Exception("Frame extraction failed.")

    return frames


# ----------------------------------------------------------
# EXTRACT AUDIO
# ----------------------------------------------------------

def extract_audio(video_path, workspace):
    audio_path = os.path.join(
        workspace["audio"],
        "audio.aac"
    )

    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        video_path,
        "-vn",
        "-acodec",
        "copy",

        audio_path
    ]

    subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    if os.path.exists(audio_path):
        return audio_path

    return None


# ----------------------------------------------------------
# BUILD LOSSLESS VIDEO
# ----------------------------------------------------------

def build_video(
    workspace,
    fps
):

    frame_pattern = os.path.join(
        workspace["frames"],
        "frame_%06d.png"
    )

    output_video = os.path.join(
        workspace["output"],
        "video.avi"
    )

    cmd = [
        "ffmpeg",
        "-y",
        "-framerate",
        str(fps),
        "-i",
        frame_pattern,
        "-c:v",
        "ffv1",
        "-pix_fmt",
        "bgr0",

        output_video
    ]

    process = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True

    )

    if process.returncode != 0:

        raise Exception(process.stderr)

    return output_video


# ----------------------------------------------------------
# MERGE AUDIO
# ----------------------------------------------------------

def merge_audio(
    video_path,
    audio_path,
    workspace

):

    if audio_path is None:
        return video_path

    final_video = os.path.join(
        workspace["output"],
        "final_output.avi"

    )

    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        video_path,
        "-i",
        audio_path,
        "-c:v",
        "copy",
        "-c:a",
        "copy",
        "-shortest",

        final_video
    ]

    process = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    if process.returncode != 0:

        raise Exception(process.stderr)

    return final_video