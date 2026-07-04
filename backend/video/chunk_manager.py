"""
StegoVault V4

Chunk Manager

Splits encrypted payload into packets
that can be embedded across multiple
video frames.

Each packet contains:

-------------------------------------------------

Magic Header
Total Packets
Packet Index
Payload Length
Payload

-------------------------------------------------

During decoding every packet is recovered,
sorted and merged back into the original
ciphertext.
"""

import math
import struct


MAGIC = b"STEGO"

HEADER_FORMAT = ">5sHHI"

HEADER_SIZE = struct.calcsize(HEADER_FORMAT)


# -------------------------------------------------------
# HEADER
# -------------------------------------------------------

def create_header(

        total_packets,

        packet_index,

        payload_size

):

    return struct.pack(

        HEADER_FORMAT,

        MAGIC,

        total_packets,

        packet_index,

        payload_size

    )


# -------------------------------------------------------
# READ HEADER
# -------------------------------------------------------

def parse_header(packet):

    if len(packet) < HEADER_SIZE:

        raise Exception("Packet too small")

    magic, total, index, size = struct.unpack(

        HEADER_FORMAT,

        packet[:HEADER_SIZE]

    )

    if magic != MAGIC:

        raise Exception("Invalid packet")

    payload = packet[HEADER_SIZE:]

    payload = payload[:size]

    return {

        "total": total,

        "index": index,

        "payload": payload

    }


# -------------------------------------------------------
# SPLIT
# -------------------------------------------------------

def split_ciphertext(

        ciphertext,

        packets

):

    if packets <= 0:

        raise Exception("Invalid packet count")

    packet_size = math.ceil(

        len(ciphertext) /

        packets

    )

    output = []

    start = 0

    for i in range(packets):

        piece = ciphertext[

            start :

            start + packet_size

        ]

        start += packet_size

        header = create_header(

            packets,

            i,

            len(piece)

        )

        output.append(

            header + piece

        )

    return output


# -------------------------------------------------------
# MERGE
# -------------------------------------------------------

def merge_packets(packet_list):

    decoded = []

    expected_total = None

    for packet in packet_list:

        info = parse_header(packet)

        if expected_total is None:

            expected_total = info["total"]

        decoded.append(

            (

                info["index"],

                info["payload"]

            )

        )

    decoded.sort(

        key=lambda x: x[0]

    )

    ciphertext = b"".join(

        [

            x[1]

            for x in decoded

        ]

    )

    return ciphertext


# -------------------------------------------------------
# VERIFY
# -------------------------------------------------------

def verify_packets(packet_list):

    indexes = []

    total = None

    for packet in packet_list:

        info = parse_header(packet)

        indexes.append(

            info["index"]

        )

        total = info["total"]

    indexes.sort()

    if indexes != list(range(total)):

        raise Exception(

            "Missing packet."

        )

    return True