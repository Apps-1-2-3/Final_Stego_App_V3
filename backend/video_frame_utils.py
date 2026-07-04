import os
import shutil
import subprocess
import tempfile


def ffmpeg_exists():
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


def create_workspace():
    root = tempfile.mkdtemp(prefix="stegovideo_")
    frames = os.path.join(root, "frames")
    os.makedirs(frames, exist_ok=True)

    return {
        "root": root,
        "frames": frames
    }


def cleanup_workspace(workspace):
    if os.path.exists(workspace["root"]):
        shutil.rmtree(workspace["root"], ignore_errors=True)


def get_video_info(video_path):
    import cv2
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        raise Exception("Unable to open video")

    fps = cap.get(cv2.CAP_PROP_FPS)

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    cap.release()

    return {
        "fps": fps,
        "width": width,
        "height": height,
        "frames": frames
    }


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

    files = sorted(

        [

            os.path.join(

                workspace["frames"],

                f

            )

            for f in os.listdir(workspace["frames"])

            if f.endswith(".png")

        ]

    )

    if len(files) == 0:

        raise Exception("No frames extracted")

    return files


def rebuild_video(
        workspace,
        fps,
        output_path
):

    frame_pattern = os.path.join(

        workspace["frames"],

        "frame_%06d.png"

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

        output_path

    ]

    process = subprocess.run(

        cmd,

        stdout=subprocess.PIPE,

        stderr=subprocess.PIPE,

        text=True

    )

    if process.returncode != 0:

        raise Exception(process.stderr)

    if not os.path.exists(output_path):

        raise Exception("Output video not created")

    if os.path.getsize(output_path) == 0:

        raise Exception("Output video is empty")

    return output_path