import streamlit as st
import pandas as pd
import numpy as np

# Load player stats from GitHub
@st.cache_data
def load_player_stats():
    url = "https://raw.githubusercontent.com/antonysamios-source/Monte3/main/parsed_tennis_dataset.csv"
    return pd.read_csv(url)

# Monte Carlo simulation of match outcome
def simulate_match(p1_win_prob, p2_win_prob, p1_score, p2_score, n_sim=100000):
    p1_wins = 0
    for _ in range(n_sim):
        score_A, score_B = p1_score, p2_score
        while score_A < 4 and score_B < 4:
            if np.random.rand() < p1_win_prob:
                score_A += 1
            else:
                score_B += 1
        if score_A > score_B:
            p1_wins += 1
    return p1_wins / n_sim

# Kelly criterion calculator
def kelly_fraction(prob, odds):
    b = odds - 1
    q = 1 - prob
    kelly = (b * prob - q) / b if b != 0 else 0
    return max(kelly, 0)

# App UI
st.title("🎾 Tennis Match Win Probability Simulator")

# Load data
df = load_player_stats()
players = sorted(set(df["player_A"]).union(df["player_B"]))

# Player selection
col1, col2 = st.columns(2)
with col1:
    player_A = st.selectbox("Select Player A", players)
with col2:
    player_B = st.selectbox("Select Player B", [p for p in players if p != player_A])

# Initialize score in session state
if "score_A" not in st.session_state:
    st.session_state.score_A = 0
if "score_B" not in st.session_state:
    st.session_state.score_B = 0

# Point buttons
st.write("### 🎯 Current Score")
st.write(f"{player_A}: {st.session_state.score_A} — {player_B}: {st.session_state.score_B}")

col3, col4 = st.columns(2)
with col3:
    if st.button(f"+1 Point {player_A}"):
        st.session_state.score_A += 1
with col4:
    if st.button(f"+1 Point {player_B}"):
        st.session_state.score_B += 1

# Get win % stats
row = df[(df["player_A"] == player_A) & (df["player_B"] == player_B)]
if row.empty:
    row = df[(df["player_A"] == player_B) & (df["player_B"] == player_A)]
    if row.empty:
        st.error("❌ No matchup data found between selected players.")
        st.stop()
    else:
        serve_win_pct_A = row["serve_win_pct_B"].values[0]
        serve_win_pct_B = row["serve_win_pct_A"].values[0]
else:
    serve_win_pct_A = row["serve_win_pct_A"].values[0]
    serve_win_pct_B = row["serve_win_pct_B"].values[0]

# Simplified win probabilities (normalize to sum 1)
total = serve_win_pct_A + serve_win_pct_B
p1_prob = serve_win_pct_A / total
p2_prob = serve_win_pct_B / total

# Monte Carlo simulation
p1_win_prob = simulate_match(p1_prob, p2_prob, st.session_state.score_A, st.session_state.score_B)
p2_win_prob = 1 - p1_win_prob

# Decimal odds
p1_odds = round(1 / p1_win_prob, 2) if p1_win_prob > 0 else float("inf")
p2_odds = round(1 / p2_win_prob, 2) if p2_win_prob > 0 else float("inf")

st.subheader("📈 Live Win Probabilities (from 100,000 simulations)")
st.write(f"🔹 {player_A}: **{p1_win_prob:.2%}** (Decimal Odds: {p1_odds})")
st.write(f"🔹 {player_B}: **{p2_win_prob:.2%}** (Decimal Odds: {p2_odds})")

# Bankroll input
bankroll = st.number_input("💰 Enter your bankroll (£)", min_value=1.0, value=1000.0, step=50.0)

# Kelly stake calculations
p1_kelly = kelly_fraction(p1_win_prob, p1_odds)
p2_kelly = kelly_fraction(p2_win_prob, p2_odds)

st.subheader("💡 Kelly Bet Sizing")
st.write(f"➡️ {player_A}: Bet **{p1_kelly*100:.2f}%** of bankroll = £{p1_kelly * bankroll:.2f}")
st.write(f"➡️ {player_B}: Bet **{p2_kelly*100:.2f}%** of bankroll = £{p2_kelly * bankroll:.2f}")

# Reset score
if st.button("🔁 Reset Score"):
    st.session_state.score_A = 0
    st.session_state.score_B = 0
