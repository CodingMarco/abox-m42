import re
import sys
import time


PROMPT_BOLT = "BOLT> "
last_buffer = ""


def get_last_buffer():
    return last_buffer


def wait_for_prompt_match(ser, prompt_regex, timeout=60):
    global last_buffer
    last_buffer = ""
    start = time.time()
    while time.time() - start < timeout:
        # There might be weird things happening over serial
        # (eg. the AP resets before everything is transmitted).
        # Therefore, we have to ignore decoding errors here.
        bytes_to_read = 1 if ser.inWaiting() == 0 else ser.inWaiting()
        new_read = ser.read(bytes_to_read).decode("utf-8", errors="ignore")
        print(new_read, end="")
        sys.stdout.flush()

        last_buffer += new_read

        match = re.search(prompt_regex, last_buffer)
        if match:
            return match.group(0)

    raise Exception(f"Timeout waiting for prompt: '{prompt_regex}'")


def init_and_configure_ip(ser):
    ser.write(b"\n")
    wait_for_prompt_match(ser, PROMPT_BOLT)
    ser.write(b"ifconfig eth0 -addr=192.168.1.1 -mask=255.255.255.0\n")
    wait_for_prompt_match(ser, PROMPT_BOLT)


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
