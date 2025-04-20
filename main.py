import streamlit as st
import sqlite3
import hashlib
import os
from cryptography.fernet import Fernet

# File to store the encryption key
KEY_FILE = "simple_Secret.key"

# Function to load or create encryption key
def load_key():
    if not os.path.exists(KEY_FILE):
        key = Fernet.generate_key()
        with open(KEY_FILE, "wb") as f:
            f.write(key)
    else:
        with open(KEY_FILE, "rb") as f:
            key = f.read()
    return key

cipher = Fernet(load_key())

# Initialize SQLite database
def init_db():
    conn = sqlite3.connect("simple_data.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS vault (
            label TEXT PRIMARY KEY,
            encrypted_key TEXT,
            passkey TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# Hashing passkey
def hash_passkey(passkey):
    return hashlib.sha256(passkey.encode()).hexdigest()

# Encrypt secret
def encrypt(text):
    return cipher.encrypt(text.encode()).decode()

# Decrypt secret
def decrypt(encrypted_text):
    return cipher.decrypt(encrypted_text.encode()).decode()


#  UI of streamlit

st.title("🔐 Secure Data Encryption")
menu = ["Store Secret", "Retrieve Secret"]
choice = st.sidebar.selectbox("Choose option", menu)

if choice == "Store Secret":
    st.header("Store a New Secret")
    label = st.text_input("Label (unique ID)")
    secret = st.text_area("Your secret")
    passkey = st.text_input("Passkey (to protect your data)", type="password")

    if st.button("Encrypt and Save"):
        if label and secret and passkey:
            conn = sqlite3.connect("simple_data.db")
            c = conn.cursor()
            encrypted = encrypt(secret)
            hashed_key = hash_passkey(passkey)

            try:
                c.execute("INSERT INTO vault (label, encrypted_key, passkey) VALUES (?, ?, ?)",
                          (label, encrypted, hashed_key))
                conn.commit()
                st.success("✅ Secret saved successfully!")
            except sqlite3.IntegrityError:
                st.error("⚠️ A secret with this label already exists.")
            conn.close()
        else:
            st.warning("Please fill all the fields.")

elif choice == "Retrieve Secret":
    st.header("Retrieve Your Secret")
    label = st.text_input("Enter the label")
    passkey = st.text_input("Enter your passkey", type="password")

    if st.button("Retrieve"):
        if label and passkey:
            conn = sqlite3.connect("simple_data.db")
            c = conn.cursor()
            c.execute("SELECT encrypted_key, passkey FROM vault WHERE label = ?", (label,))
            result = c.fetchone()
            conn.close()

            if result:
                stored_encrypted, stored_hashed_key = result
                if hash_passkey(passkey) == stored_hashed_key:
                    try:
                        decrypted = decrypt(stored_encrypted)
                        st.success("🔓 Your Secret:")
                        st.code(decrypted)
                    except Exception as e:
                        st.error("Decryption failed.")
                else:
                    st.error("Incorrect passkey!")
            else:
                st.error("No secret found with this label.")
        else:
            st.warning("Please enter both label and passkey.")
