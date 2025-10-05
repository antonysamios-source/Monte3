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
st.title("🎾 Live Tennis Match Simulator + Kelly Betting")

col1, col2 = st.columns(2)
with col1:
    player_A = st.selectbox("Select Player A", players)
with col2:
    player_B = st.selectbox("Select Player B", [p for p in players if p != player_A])

# ---------- UI: MATCH FORMAT & SERVER ----------
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

# ---------- POINT LABELS ----------
POINT_LABELS = ["0", "15", "30", "40", "Ad"]

def point_label(p):
    return POINT_LABELS[min(p, 4)]

# ---------- DISPLAY LIVE SCORE ----------
st.subheader("📺 Live Score")
st.markdown(f"**Set Score:** {player_A} {st.session_state.score['sets_A']} - {st.session_state.score['sets_B']} {player_B}")
st.markdown(f"**Game Score:** {player_A} {st.session_state.score['games_A']} - {st.session_state.score['games_B']} {player_B}")
st.markdown(f"**Point Score:** {player_A} {point_label(st.session_state.score['points_A'])} - {point_label(st.session_state.score['points_B'])} {player_B}")
st.markdown(f"**Serving:** 🎾 {st.session_state.score['serving']}")

# ---------- POINT BUTTONS ----------
col5, col6 = st.columns(2)
with col5:
    if st.button(f"+1 Point {player_A}"):
        st.session_state.score["points_A"] += 1
with col6:
    if st.button(f"+1 Point {player_B}"):
        st.session_state.score["points_B"] += 1

# ---------- RESET ----------
if st.button("🔁 Reset Match"):
    st.session_state.score = {
        "sets_A": 0, "sets_B": 0,
        "games_A": 0, "games_B": 0,
        "points_A": 0, "points_B": 0,
        "serving": server
    }

# ---------- WINNER CHECK ----------
def check_game_win(points_A, points_B):
    if points_A >= 4 and points_A - points_B >= 2:
        return "A"
    elif points_B >= 4 and points_B - points_A >= 2:
        return "B"
    return None

def check_set_win(games_A, games_B):
    if games_A >= 6 and games_A - games_B >= 2:
        return "A"
    elif games_B >= 6 and games_B - games_A >= 2:
        return "B"
    return None

def update_score():
    winner = check_game_win(st.session_state.score["points_A"], st.session_state.score["points_B"])
    if winner:
        if winner == "A":
            st.session_state.score["games_A"] += 1
        else:
            st.session_state.score["games_B"] += 1

        # Reset points
        st.session_state.score["points_A"] = 0
        st.session_state.score["points_B"] = 0
        st.session_state.score["serving"] = player_B if st.session_state.score["serving"] == player_A else player_A

        # Check for set win
        set_winner = check_set_win(st.session_state.score["games_A"], st.session_state.score["games_B"])
        if set_winner:
            if set_winner == "A":
                st.session_state.score["sets_A"] += 1
            else:
                st.session_state.score["sets_B"] += 1
            st.session_state.score["games_A"] = 0
            st.session_state.score["games_B"] = 0

# ---------- AUTO UPDATE SCORE ----------
update_score()

# ---------- WIN PROBABILITIES ----------
row = df[(df["player_A"] == player_A) & (df["player_B"] == player_B)]
if row.empty:
    row = df[(df["player_A"] == player_B) & (df["player_B"] == player_A)]
    if row.empty:
        st.error("❌ No matchup data found between selected players.")
        st.stop()
    else:
        serve_A = row["serve_win_pct_B"].values[0]
        serve_B = row["serve_win_pct_A"].values[0]
else:
    serve_A = row["serve_win_pct_A"].values[0]
    serve_B = row["serve_win_pct_B"].values[0]

# Normalize
total = serve_A + serve_B
p_A = serve_A / total
p_B = serve_B / total

# ---------- MONTE CARLO MATCH SIM ----------
def simulate_full_match(p_A, p_B, best_of=3):
    win_A = 0
    for _ in range(N_SIMULATIONS):
        sets_A, sets_B = 0, 0
        while sets_A < (best_of // 2 + 1) and sets_B < (best_of // 2 + 1):
            games_A, games_B = 0, 0
            while True:
                points_A, points_B = 0, 0
                while True:
                    if random.random() < p_A:
                        points_A += 1
                    else:
                        points_B += 1
                    if points_A >= 4 and points_A - points_B >= 2:
                        games_A += 1
                        break
                    elif points_B >= 4 and points_B - points_A >= 2:
                        games_B += 1
                        break
                if (games_A >= 6 or games_B >= 6) and abs(games_A - games_B) >= 2:
                    break
            if games_A > games_B:
                sets_A += 1
            else:
                sets_B += 1
        if sets_A > sets_B:
            win_A += 1
    return win_A / N_SIMULATIONS

best_of = 3 if match_format == "Best of 3" else 5
win_prob_A = simulate_full_match(p_A, p_B, best_of=best_of)
win_prob_B = 1 - win_prob_A

# ---------- ODDS + KELLY ----------
odds_A = round(1 / win_prob_A, 2)
odds_B = round(1 / win_prob_B, 2)

def kelly(prob, odds):
    b = odds - 1
    q = 1 - prob
    k = (b * prob - q) / b if b > 0 else 0
    return max(k, 0)

bankroll = st.number_input("💰 Enter your bankroll (£)", min_value=1.0, value=1000.0, step=50.0)
kelly_A = kelly(win_prob_A, odds_A)
kelly_B = kelly(win_prob_B, odds_B)

# ---------- DISPLAY RESULTS ----------
st.subheader("📈 Monte Carlo Win Probabilities")
st.write(f"🔹 {player_A}: **{win_prob_A:.2%}** (Decimal Odds: {odds_A}) — Kelly Bet: £{kelly_A * bankroll:.2f}")
st.write(f"🔹 {player_B}: **{win_prob_B:.2%}** (Decimal Odds: {odds_B}) — Kelly Bet: £{kelly_B * bankroll:.2f}")
