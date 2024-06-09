import re
import sys
import time
import serial
import logging
from pathlib import Path


PROMPT_BOLT = "BOLT> "
MAX_RAM_USABLE = 0x6000000


def wait_for_prompt_match(ser, prompt_regex, timeout=60):
    buffer = ""
    start = time.time()
    while time.time() - start < timeout:
        # There might be weird things happening over serial
        # (eg. the AP resets before everything is transmitted).
        # Therefore, we have to ignore decoding errors here.
        bytes_to_read = 1 if ser.inWaiting() == 0 else ser.inWaiting()
        new_read = ser.read(bytes_to_read).decode("utf-8", errors="ignore")
        print(new_read, end="")
        sys.stdout.flush()

        buffer += new_read

        match = re.search(prompt_regex, buffer)
        if match:
            return match.group(0)

    raise Exception(f"Timeout waiting for prompt: '{prompt_regex}'")


def load_partitions():
    with open("partitions.txt", "r") as f:
        lines = f.readlines()

    for line in lines:
        line = line.strip()
        part_name = line.split()[0]

        # regex to match eg. "emmcflash0.rwfs  EMMC flash Data : 0x036100000-0x05E100000 (640MB)" and extract start and end address
        part_regex = f"{part_name}.*: 0x([0-9A-F]+)-0x([0-9A-F]+)"
        part_match = re.search(part_regex, line)

        start = int(part_match.group(1), 16)
        end = int(part_match.group(2), 16)
        size = end - start

        yield part_name, start, end, size


def main():
    tftp_dir = Path("tftp")
    with serial.Serial("/dev/ttyUSB0", 115200, timeout=1) as ser:
        ser.write(b"\n")
        wait_for_prompt_match(ser, PROMPT_BOLT)
        ser.write(b"ifconfig eth0 -addr=192.168.1.1 -mask=255.255.255.0\n")
        wait_for_prompt_match(ser, PROMPT_BOLT)

        for part_name, start, end, size in load_partitions():
            device = part_name.split(".")[0]

            # cmd to load partition into memory: load -raw -offset=<offset inside device> -max=<number of bytes to read> <device>

            # Load in chunks of MAX_RAM_USABLE
            for offset in range(0, size, MAX_RAM_USABLE):
                print(f"------------- Loading {part_name} at 0x{start+offset:X}")

                length = min(MAX_RAM_USABLE, size - offset)
                cmd_load = (
                    f"load -raw -offset=0x{start+offset:X} -max=0x{length:X} {device}"
                )
                ser.write(f"{cmd_load}\n".encode("utf-8"))
                wait_for_prompt_match(ser, PROMPT_BOLT)

                cmd_save = f"save 192.168.1.10:tmp.bin 0x8000 0x{length:X}"
                ser.write(f"{cmd_save}\n".encode("utf-8"))
                wait_for_prompt_match(ser, PROMPT_BOLT)

                saved_file = tftp_dir / "tmp.bin"
                out_file = tftp_dir / f"{part_name}.bin"

                with open(saved_file, "rb") as f:
                    with open(out_file, "ab") as out_f:
                        out_f.write(f.read())

                saved_file.unlink()


if __name__ == "__main__":
    main()
