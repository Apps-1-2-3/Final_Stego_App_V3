import math


HEADER = b"STEGO"


def split_bytes(data: bytes, chunk_size: int):
    """
    Split bytes into equal chunks.
    """

    return [
        data[i:i + chunk_size]
        for i in range(0, len(data), chunk_size)
    ]


def merge_chunks(chunks):

    return b"".join(chunks)


def create_header(total_chunks: int, chunk_index: int):

    """
    4 bytes  : STEGO magic
    2 bytes  : total chunks
    2 bytes  : current chunk index
    """

    return (
        HEADER +
        total_chunks.to_bytes(2, "big") +
        chunk_index.to_bytes(2, "big")
    )


def parse_header(blob: bytes):

    if len(blob) < 8:
        raise Exception("Invalid header")

    if blob[:5] != HEADER:
        raise Exception("Header mismatch")

    total = int.from_bytes(blob[5:7], "big")

    index = int.from_bytes(blob[7:9], "big")

    payload = blob[9:]

    return total, index, payload


def make_chunks(ciphertext: bytes, frames_available: int):

    """
    Decide chunk size automatically.
    """

    usable_frames = max(1, frames_available)

    chunk_size = math.ceil(
        len(ciphertext) / usable_frames
    )

    payloads = split_bytes(
        ciphertext,
        chunk_size
    )

    output = []

    total = len(payloads)

    for idx, payload in enumerate(payloads):

        packet = (
            create_header(total, idx)
            + payload
        )

        output.append(packet)

    return output


def rebuild_payload(chunks):

    """
    Chunks:
    [
        (index, payload),
        ...
    ]
    """

    chunks = sorted(
        chunks,
        key=lambda x: x[0]
    )

    return merge_chunks(
        [
            c[1]
            for c in chunks
        ]
    )