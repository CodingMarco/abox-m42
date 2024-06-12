import utils
import serial
import argparse
from pathlib import Path


# Flash command: flash -offset=0x00C100000 -size=512 192.168.1.10:data.bin emmcflash0

MAX_CHUNK_SIZE = 16 * 1024 * 1024 - 1


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("binary", type=Path, help="Binary file to write to flash")

    partiton_names = [t[0] for t in utils.load_partitions()]
    parser.add_argument(
        "partition", type=str, help="Partition to write data to", choices=partiton_names
    )

    return parser.parse_args()


def flash_partition(ser, binary, partition, part_name):
    part_start, part_end, part_size = partition
    part_device = part_name.split(".")[0]

    with open(binary, "rb") as f:
        data = f.read()

    # Write data in chunks of max size MAX_CHUNK_SIZE. Copy to "tftp/" dir, then flash
    for offset in range(0, len(data), MAX_CHUNK_SIZE):
        chunk = data[offset : offset + MAX_CHUNK_SIZE]
        with open("tftp/data.bin", "wb") as f:
            f.write(chunk)

        offset_hex = f"0x{part_start + offset:08X}"

        flash_cmd = f"flash -offset={offset_hex} 192.168.1.10:data.bin {part_device}\n"
        ser.write(flash_cmd.encode("utf-8"))
        utils.wait_for_prompt_match(ser, utils.PROMPT_BOLT)


def main():
    args = parse_args()
    partitions = list(utils.load_partitions())
    partitions = {p[0]: p[1:] for p in partitions}

    with serial.Serial("/dev/ttyUSB0", 115200, timeout=1) as ser:
        utils.init_and_configure_ip(ser)
        flash_partition(ser, args.binary, partitions[args.partition], args.partition)


if __name__ == "__main__":
    main()
