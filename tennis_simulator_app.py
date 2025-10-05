import streamlit as st
import pandas as pd
import numpy as np
import random

N_SIMULATIONS = 100000

@st.cache_data
def load_player_stats():
    url = "https://raw.githubusercontent.com/antonysamios-source/Monte3/main/parsed_tennis_dataset.csv"
    return pd.read_csv(url)

# ----------------- UI ------------------
df = load_player_stats()
players = sorted(set(df["player_A"]).union(df["player_B"]))

st.title("🎾 Monte Carlo Tennis Betting Simulator")

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

# Optional: Manual override starting odds
st.markdown("### 🎯 Optional: Override Starting Odds (Decimal)")
override_A = st.number_input(f"{player_A} starting odds (decimal)", value=0.0)
override_B = st.number_input(f"{player_B} starting odds (decimal)", value=0.0)

# Bankroll input
bankroll = st.number_input("💰 Enter your bankroll (£)", value=1000.0)

# ----------------- Session State ------------------
if "score" not in st.session_state:
    st.session_state.score = {
        "sets_A": 0, "sets_B": 0,
        "games_A": 0, "games_B": 0,
        "points_A": 0, "points_B": 0,
        "serving": server
    }

POINT_LABELS = ["0", "15", "30", "40", "Ad"]
def point_label(p): return POINT_LABELS[min(p, 4)]

# ----------------- Buttons ------------------
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

# ----------------- Display Score ------------------
st.markdown(f"### 📺 Current Score")
st.markdown(f"**Set Score:** {player_A} {st.session_state.score['sets_A']} - {st.session_state.score['sets_B']} {player_B}")
st.markdown(f"**Game Score:** {player_A} {st.session_state.score['games_A']} - {st.session_state.score['games_B']} {player_B}")
st.markdown(f"**Point Score:** {player_A} {point_label(st.session_state.score['points_A'])} - {point_label(st.session_state.score['points_B'])} {player_B}")
st.markdown(f"**Serving:** 🎾 {st.session_state.score['serving']}")

# ----------------- Simulation Engine ------------------
def simulate_match_from_state(pA, pB, score, best_of):
    win_A = 0
    for _ in range(N_SIMULATIONS):
        sets_A = score["sets_A"]
        sets_B = score["sets_B"]
        games_A = score["games_A"]
        games_B = score["games_B"]
        points_A = score["points_A"]
        points_B = score["points_B"]
        serving = score["serving"]

        sA, sB = sets_A, sets_B
        gA, gB = games_A, games_B
        pA_, pB_ = points_A, points_B
        server = serving

        while sA < (3 if best_of == "Best of 5" else 2) and sB < (3 if best_of == "Best of 5" else 2):
            if random.random() < (pA if server == player_A else pB):
                pA_ += 1
            else:
                pB_ += 1

            if (pA_ >= 4 and pA_ - pB_ >= 2):
                gA += 1
                pA_, pB_ = 0, 0
                server = player_B if server == player_A else player_A
            elif (pB_ >= 4 and pB_ - pA_ >= 2):
                gB += 1
                pA_, pB_ = 0, 0
                server = player_B if server == player_A else player_A

            if gA >= 6 and gA - gB >= 2:
                sA += 1
                gA, gB = 0, 0
            elif gB >= 6 and gB - gA >= 2:
                sB += 1
                gA, gB = 0, 0

        if sA > sB:
            win_A += 1

    return win_A / N_SIMULATIONS

# ----------------- Get Base Win Probabilities ------------------
pA_row = df[(df["player_A"] == player_A) & (df["player_B"] == player_B)]
pB_row = df[(df["player_A"] == player_B) & (df["player_B"] == player_A)]

if not pA_row.empty and not pB_row.empty:
    pA_win_pct = float(pA_row["pA_svpt_won"])
    pB_win_pct = float(pB_row["pA_svpt_won"])
else:
    pA_win_pct = pB_win_pct = 0.63  # fallback

# ----------------- Implied Probabilities at Match Start ------------------
if override_A > 1.01 and override_B > 1.01:
    implied_start_prob_A = 1 / override_A
    implied_start_prob_B = 1 / override_B
else:
    implied_start_prob_A = simulate_match_from_state(pA_win_pct, pB_win_pct, {
        "sets_A": 0, "sets_B": 0,
        "games_A": 0, "games_B": 0,
        "points_A": 0, "points_B": 0,
        "serving": server
    }, match_format)
    implied_start_prob_B = 1 - implied_start_prob_A

# ----------------- Simulate from Current Score ------------------
live_prob_A = simulate_match_from_state(pA_win_pct, pB_win_pct, st.session_state.score, match_format)
live_prob_B = 1 - live_prob_A

odds_A = round(1 / live_prob_A, 2) if live_prob_A > 0 else float("inf")
odds_B = round(1 / live_prob_B, 2) if live_prob_B > 0 else float("inf")

# Safe Kelly calculation
def calculate_kelly(prob, odds):
    if odds <= 1.0:
        return 0.0
    k = (prob * odds - 1) / (odds - 1)
    return max(0.0, round(k, 3))

kelly_A = calculate_kelly(live_prob_A, odds_A)
kelly_B = calculate_kelly(live_prob_B, odds_B)
stake_A = round(kelly_A * bankroll, 2)
stake_B = round(kelly_B * bankroll, 2)

# ----------------- Display Results ------------------
st.markdown("### 🎯 Starting Win Probabilities")
st.markdown(f"**{player_A}:** {implied_start_prob_A:.2%}")
st.markdown(f"**{player_B}:** {implied_start_prob_B:.2%}")

st.markdown("---")
st.markdown("### 📈 Live Win Probabilities (Simulated)")
st.markdown(f"**{player_A}:** {live_prob_A:.2%} (odds: {odds_A}) — Stake: £{stake_A}")
st.markdown(f"**{player_B}:** {live_prob_B:.2%} (odds: {odds_B}) — Stake: £{stake_B}")
st.markdown("---")
st.markdown("📌 *100,000 Monte Carlo simulations from current score.*")
