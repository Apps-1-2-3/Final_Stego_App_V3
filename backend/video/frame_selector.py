"""
StegoVault V4

Adaptive Frame Selection

Chooses the best frames for embedding based on
image complexity instead of fixed positions.

Higher complexity
↓

Better imperceptibility

↓

Harder steganalysis
"""

import random
import hashlib

import cv2
import numpy as np

from PIL import Image


# -----------------------------------------------------
# EDGE SCORE
# -----------------------------------------------------

def edge_score(image):

    if isinstance(image, Image.Image):

        gray = np.array(
            image.convert("L")
        )

    else:

        gray = image

    edges = cv2.Canny(

        gray,

        80,

        180

    )

    return float(np.mean(edges))


# -----------------------------------------------------
# VARIANCE SCORE
# -----------------------------------------------------

def variance_score(image):

    if isinstance(image, Image.Image):

        gray = np.array(
            image.convert("L")
        )

    else:

        gray = image

    return float(np.var(gray))


# -----------------------------------------------------
# ENTROPY
# -----------------------------------------------------

def entropy_score(image):

    if isinstance(image, Image.Image):

        gray = np.array(
            image.convert("L")
        )

    else:

        gray = image

    hist = cv2.calcHist(
        [gray],
        [0],
        None,
        [256],
        [0,256]
    )

    hist /= hist.sum()

    hist = hist.flatten()

    hist = hist[hist > 0]

    entropy = -np.sum(

        hist *

        np.log2(hist)

    )

    return float(entropy)


# -----------------------------------------------------
# FINAL SCORE
# -----------------------------------------------------

def frame_score(image):

    edge = edge_score(image)

    variance = variance_score(image)

    entropy = entropy_score(image)

    score = (

        edge * 0.45 +

        variance * 0.25 +

        entropy * 30

    )

    return {

        "edge": edge,

        "variance": variance,

        "entropy": entropy,

        "score": score

    }


# -----------------------------------------------------
# PASSWORD RNG
# -----------------------------------------------------

def password_seed(password):

    digest = hashlib.sha256(

        password.encode()

    ).digest()

    return int.from_bytes(

        digest,

        "big"

    )


# -----------------------------------------------------
# ADAPTIVE FRAME CHOICE
# -----------------------------------------------------

def choose_frames(

        frame_paths,

        password,

        required_frames

):

    scored = []

    for index, path in enumerate(frame_paths):

        image = Image.open(path)

        score = frame_score(image)

        scored.append(

            (

                index,

                score["score"]

            )

        )

    scored.sort(

        key=lambda x: x[1],

        reverse=True

    )

    candidates = scored[:max(

        required_frames * 3,

        required_frames

    )]

    rng = random.Random(

        password_seed(password)

    )

    rng.shuffle(candidates)

    chosen = sorted(

        [

            x[0]

            for x in candidates[:required_frames]

        ]
    )

    return chosen