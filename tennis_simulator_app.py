import streamlit as st
import pandas as pd
import numpy as np
import random

# ---------- CONFIG ----------
N_SIMULATIONS = 100000

# ---------- LOAD PLAYER DATA ----------
@st.cache_data
def load_player_stats():
    url = "https://raw.githubusercontent.com/antonysamios-source/Monte3/main/parsed_tennis_dataset.csv"
    return pd.read_csv(url)

df = load_player_stats()
players = sorted(set(df["player_A"]).union(df["player_B"]))

# ---------- UI: PLAYER SELECTION ----------
st.title("🎾 Live Tennis Match Simulator (with Kelly)")

col1, col2 = st.columns(2)
with col1:
    player_A = st.selectbox("Select Player A", players)
with col2:
    player_B = st.selectbox("Select Player B", [p for p in players if p != player_A])

col3, col4 = st.columns(2)
with col3:
    match_format = st.radio("Match Format", ["Best of 3", "Best of 5"])
with col4:
    server = st.radio("Who is serving?", [player_A, player_B])

# ---------- SESSION STATE ----------
if "score" not in st.session_state:
    st.session_state.score = {
        "sets_A": 0, "sets_B": 0,
        "games_A": 0, "games_B": 0,
        "points_A": 0, "points_B": 0,
        "serving": server
    }

POINT_LABELS = ["0", "15", "30", "40", "Ad"]
def point_label(p): return POINT_LABELS[min(p, 4)]

# ---------- DISPLAY SCORE ----------
st.subheader("📺 Live Score")
st.markdown(f"**Set Score:** {player_A} {st.session_state.score['sets_A']} - {st.session_state.score['sets_B']} {player_B}")
st.markdown(f"**Game Score:** {player_A} {st.session_state.score['games_A']} - {st.session_state.score['games_B']} {player_B}")
st.markdown(f"**Point Score:** {player_A} {point_label(st.session_state.score['points_A'])} - {point_label(st.session_state.score['points_B'])} {player_B}")
st.markdown(f"**Serving:** 🎾 {st.session_state.score['serving']}")

col5, col6 = st.columns(2)
with col5:
    if st.button(f"+1 Point {player_A}"):
        st.session_state.score["points_A"] += 1
with col6:
    if st.button(f"+1 Point {player_B}"):
        st.session_state.score["points_B"] += 1

if st.button("🔁 Reset Match"):
    st.session_state.score = {
        "sets_A": 0, "sets_B": 0,
        "games_A": 0, "games_B": 0,
        "points_A": 0, "points_B": 0,
        "serving": server
    }
