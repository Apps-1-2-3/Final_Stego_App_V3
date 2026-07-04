"""
StegoVault Video Engine

Frame Manager

Responsible for

- Video Information
- Loading Frames
- Saving Frames
- Capacity Validation
"""

import os
import cv2

import numpy as np

from PIL import Image


# ---------------------------------------------------------
# VIDEO INFORMATION
# ---------------------------------------------------------

def get_video_info(video_path):

    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        raise Exception("Cannot open video.")

    info = {

        "fps": float(
            cap.get(cv2.CAP_PROP_FPS)
        ),

        "width": int(
            cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        ),

        "height": int(
            cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        ),

        "frame_count": int(
            cap.get(cv2.CAP_PROP_FRAME_COUNT)
        )

    }

    cap.release()

    return info


# ---------------------------------------------------------
# FRAME LOADING
# ---------------------------------------------------------

def load_frame(frame_path):

    if not os.path.exists(frame_path):

        raise Exception(
            f"Frame not found: {frame_path}"
        )

    return Image.open(frame_path).convert("RGB")


# ---------------------------------------------------------
# SAVE FRAME
# ---------------------------------------------------------

def save_frame(image, frame_path):

    image.save(

        frame_path,

        format="PNG",

        optimize=False

    )


# ---------------------------------------------------------
# PIL -> OpenCV
# ---------------------------------------------------------

def pil_to_cv(image):

    rgb = np.array(image)

    return cv2.cvtColor(

        rgb,

        cv2.COLOR_RGB2BGR

    )


# ---------------------------------------------------------
# OpenCV -> PIL
# ---------------------------------------------------------

def cv_to_pil(frame):

    rgb = cv2.cvtColor(

        frame,

        cv2.COLOR_BGR2RGB

    )

    return Image.fromarray(rgb)


# ---------------------------------------------------------
# ESTIMATE IMAGE CAPACITY
# ---------------------------------------------------------

def image_capacity(image):

    w, h = image.size

    pixels = w * h

    bits = pixels * 3

    bytes_capacity = bits // 8

    return {

        "pixels": pixels,

        "bits": bits,

        "bytes": bytes_capacity

    }


# ---------------------------------------------------------
# VALIDATE PAYLOAD
# ---------------------------------------------------------

def validate_payload(image, payload):

    cap = image_capacity(image)

    if len(payload) > cap["bytes"]:

        raise Exception(

            f"Payload too large.\n"
            f"Capacity : {cap['bytes']} bytes\n"
            f"Payload  : {len(payload)} bytes"

        )

    return True


# ---------------------------------------------------------
# GET FRAME PATH
# ---------------------------------------------------------

def frame_path(frames, index):

    if index < 0:

        raise Exception("Negative frame index")

    if index >= len(frames):

        raise Exception("Frame index exceeds total frames")

    return frames[index]