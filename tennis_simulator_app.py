
import streamlit as st
import pandas as pd
import numpy as np
from fractions import Fraction

st.set_page_config(page_title="Tennis Monte Carlo Simulator", layout="centered")

@st.cache_data
def load_player_stats():
    df = pd.read_csv("parsed_tennis_dataset.csv")
    p1_stats = df[['player_A', 'serve_win_pct_A']].rename(columns={'player_A': 'player', 'serve_win_pct_A': 'serve_win'})
    p2_stats = df[['player_B', 'serve_win_pct_B']].rename(columns={'player_B': 'player', 'serve_win_pct_B': 'serve_win'})
    all_stats = pd.concat([p1_stats, p2_stats])
    return all_stats.groupby('player').agg({'serve_win': 'mean'}).reset_index()

def to_fractional(p):
    if p == 0:
        return "∞"
    frac = Fraction((1 / p) - 1).limit_denominator(100)
    return f"{frac.numerator}/{frac.denominator}"

class TennisMatchSimulator:
    def __init__(self, p1_name, p2_name, p1_serve_win, p2_serve_win):
        self.p1 = p1_name
        self.p2 = p2_name
        self.p1_serve_win = p1_serve_win
        self.p2_serve_win = p2_serve_win
        self.p1_pts = 0
        self.p2_pts = 0
        self.odds_history = []

    def simulate_match(self, n=10000):
        p1_wins = 0
        for _ in range(n):
            if self._simulate_bo3():
                p1_wins += 1
        p1_prob = p1_wins / n
        p2_prob = 1 - p1_prob
        return p1_prob, p2_prob

    def _simulate_bo3(self):
        p1_sets = 0
        p2_sets = 0
        while p1_sets < 2 and p2_sets < 2:
            if self._simulate_set():
                p1_sets += 1
            else:
                p2_sets += 1
        return p1_sets > p2_sets

    def _simulate_set(self):
        p1_games = p2_games = 0
        server = 0
        while True:
            win = np.random.rand() < (self.p1_serve_win if server == 0 else self.p2_serve_win)
            if win:
                if server == 0:
                    p1_games += 1
                else:
                    p2_games += 1
            else:
                if server == 0:
                    p2_games += 1
                else:
                    p1_games += 1
            if p1_games >= 6 and (p1_games - p2_games) >= 2:
                return True
            if p2_games >= 6 and (p2_games - p1_games) >= 2:
                return False
            if p1_games == 6 and p2_games == 6:
                return np.random.choice([True, False])
            server = 1 - server

    def score_point(self, winner):
        if winner == self.p1:
            self.p1_pts += 1
        else:
            self.p2_pts += 1

    def current_score(self):
        return f"{self.p1} {self.p1_pts} - {self.p2_pts} {self.p2}"

    def display_odds(self):
        p1_prob, p2_prob = self.simulate_match(n=5000)
        return {
            self.p1: {"prob": round(p1_prob, 4), "odds": to_fractional(p1_prob)},
            self.p2: {"prob": round(p2_prob, 4), "odds": to_fractional(p2_prob)}
        }

# Load and display
st.title("🎾 Tennis Monte Carlo Odds Simulator")

stats_df = load_player_stats()
players = stats_df['player'].tolist()

p1 = st.selectbox("Select Player A", players, index=0)
p2 = st.selectbox("Select Player B", players, index=1)

p1_serve = stats_df[stats_df['player'] == p1]['serve_win'].values[0]
p2_serve = stats_df[stats_df['player'] == p2]['serve_win'].values[0]

simulator = TennisMatchSimulator(p1, p2, p1_serve, p2_serve)

if st.button("🎲 Simulate 100,000 Matches"):
    p1_prob, p2_prob = simulator.simulate_match(n=100000)
    st.markdown(f"**Fair Odds** (No Margin):")
    st.write(f"{p1}: {to_fractional(p1_prob)} ({round(p1_prob*100, 2)}%)")
    st.write(f"{p2}: {to_fractional(p2_prob)} ({round(p2_prob*100, 2)}%)")

st.subheader("📈 Live Match Simulation")

col1, col2 = st.columns(2)
if col1.button(f"{p1} scores a point"):
    simulator.score_point(p1)
if col2.button(f"{p2} scores a point"):
    simulator.score_point(p2)

st.markdown(f"**Current Score:** {simulator.current_score()}")

live_odds = simulator.display_odds()
st.markdown("### 📊 Live Odds (Updated Every Point)")
for player, info in live_odds.items():
    st.write(f"{player}: {info['odds']} ({info['prob']*100:.2f}%)")
