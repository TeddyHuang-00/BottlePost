import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(
    "Just a Christmas tree", page_icon="🎄", initial_sidebar_state="collapsed"
)

if "auth" not in st.session_state:
    st.session_state["auth"] = False

if not st.session_state["auth"]:
    with st.form("login"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.form_submit_button("Submit"):
            if (
                username in st.secrets["root"]
                and password == st.secrets["root"][username]
            ):
                st.session_state["auth"] = True
                st.experimental_rerun()
            else:
                st.error("Incorrect username or password")
    st.stop()

DATA_FILE = "data/bottles.csv"

df = pd.read_csv(DATA_FILE)
st.dataframe(df, use_container_width=True)
st.download_button(
    "Download",
    df.to_csv(index=False).encode("utf-8"),
    "comments_" + datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".csv",
)

with st.form("upload"):
    file = st.file_uploader("Upload a CSV file")
    if st.form_submit_button("Submit"):
        if file is not None:
            new_df = pd.read_csv(file)
            new_df.to_csv(DATA_FILE, index=False)
            st.experimental_rerun()
        else:
            st.error("No file uploaded")

st.button("Rerun")
