import serial
from utils import wait_for_prompt_match, PROMPT_BOLT, get_last_buffer


def main():
    with open("commands.txt", "r") as f:
        lines = f.readlines()

    commands = [line.split(".")[0].strip() for line in lines]

    helps = ""

    with serial.Serial("/dev/ttyUSB0", 115200, timeout=1) as ser:
        ser.write(b"\n")
        wait_for_prompt_match(ser, PROMPT_BOLT)
        for cmd in commands:
            ser.write(f"help {cmd}\n".encode("utf-8"))
            wait_for_prompt_match(ser, PROMPT_BOLT)
            helps += get_last_buffer() + "\n"

    with open("helps.txt", "w") as f:
        f.write(helps)


if __name__ == "__main__":
    main()
