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
