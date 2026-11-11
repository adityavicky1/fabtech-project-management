import random
import streamlit as st

# --- PAGE CONFIGURATION (WIDE LAYOUT) ---
st.set_page_config(
    page_title="Mommy & Baby Animal Match", page_icon="🐾", layout="wide"
)

# --- CUSTOM CSS FOR BIGGER, TODDLER-FRIENDLY BUTTONS & WIDER SCREEN ---
st.markdown(
    """
    <style>
    .stButton>button {
        font-size: 26px !important;
        padding: 28px !important;
        border-radius: 20px !important;
        font-weight: bold;
        width: 100%;
        box-shadow: 0px 4px 8px rgba(0,0,0,0.15);
    }
    .big-title {
        font-size: 3em !important;
        text-align: center;
        color: #2e7d32;
        font-weight: bold;
    }
    .instruction-text {
        font-size: 1.6em !important;
        text-align: center;
        color: #444;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- PASSWORD AUTHENTICATION SETUP ---
APP_PASSWORD = "admin"

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.markdown(
        "<h2 style='text-align: center;'>🔐 Parent Login</h2>",
        unsafe_allow_html=True,
    )
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            entered_password = st.text_input(
                "Enter Password (default: admin)", type="password"
            )
            submit_btn = st.form_submit_button("Enter Game")
            if submit_btn:
                if entered_password == APP_PASSWORD:
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("Incorrect password. Try again.")
    st.stop()  # Stop execution until authenticated

# --- 10 ANIMAL PAIRS DATABASE ---
ANIMAL_PAIRS = [
    {"baby": "Puppy 🐶", "mommy": "Dog 🐕"},
    {"baby": "Kitten 🐱", "mommy": "Cat 🐈"},
    {"baby": "Calf 🐮", "mommy": "Cow 🐄"},
    {"baby": "Chick 🐥", "mommy": "Chicken 🐔"},
    {"baby": "Piglet 🐷", "mommy": "Pig 🐖"},
    {"baby": "Duckling 🦆", "mommy": "Duck 🦆"},
    {"baby": "Foal 🐴", "mommy": "Horse 🐎"},
    {"baby": "Lamb 🐑", "mommy": "Sheep 🐏"},
    {"baby": "Kid 🐐", "mommy": "Goat 🐐"},
    {"baby": "Cub 🦁", "mommy": "Lion 🦁"},
]

# Initialize Session State
if "match_score" not in st.session_state:
    st.session_state.match_score = 0
if "current_pair" not in st.session_state:
    st.session_state.current_pair = random.choice(ANIMAL_PAIRS)
    all_mommies = [p["mommy"] for p in ANIMAL_PAIRS]
    correct_mommy = st.session_state.current_pair["mommy"]
    other_mommies = [m for m in all_mommies if m != correct_mommy]
    options = random.sample(other_mommies, 3) + [correct_mommy]
    random.shuffle(options)
    st.session_state.current_options = options

# --- MAIN APP UI ---
st.markdown(
    "<h1 class='big-title'>🐾 Mommy & Baby Animal Matching Game 🐾</h1>",
    unsafe_allow_html=True,
)
st.markdown(
    "<p class='instruction-text'>Can you match the cute baby with its Mommy?</p>",
    unsafe_allow_html=True,
)
st.markdown("---")

current = st.session_state.current_pair

# Display Baby Animal Banner
st.markdown(
    f"<div style='text-align: center; padding: 30px; background-color: #e8f5e9; border-radius: 20px; margin-bottom: 30px;'>"
    f"<h2 style='color: #1b5e20; font-size: 2.2em;'>Baby: <b>{current['baby']}</b></h2>"
    f"<h3 style='color: #388e3c;'>Who is the Mommy? 🤔</h3>"
    f"</div>",
    unsafe_allow_html=True,
)

# 4 Interactive Big Choice Buttons in a 2x2 Grid
options = st.session_state.current_options
col1, col2 = st.columns(2)

with col1:
    if st.button(options[0], key="opt_0"):
        if options[0] == current["mommy"]:
            st.balloons()
            st.success(f"🎉 Yay! The Mommy of the {current['baby']} is the {options[0]}!")
            st.session_state.match_score += 1
            st.session_state.current_pair = random.choice(ANIMAL_PAIRS)
            all_mommies = [p["mommy"] for p in ANIMAL_PAIRS]
            correct_mommy = st.session_state.current_pair["mommy"]
            other_mommies = [m for m in all_mommies if m != correct_mommy]
            new_opts = random.sample(other_mommies, 3) + [correct_mommy]
            random.shuffle(new_opts)
            st.session_state.current_options = new_opts
            st.rerun()
        else:
            st.error("❌ Oops! Try another Mommy.")

    if st.button(options[1], key="opt_1"):
        if options[1] == current["mommy"]:
            st.balloons()
            st.success(f"🎉 Yay! The Mommy of the {current['baby']} is the {options[1]}!")
            st.session_state.match_score += 1
            st.session_state.current_pair = random.choice(ANIMAL_PAIRS)
            all_mommies = [p["mommy"] for p in ANIMAL_PAIRS]
            correct_mommy = st.session_state.current_pair["mommy"]
            other_mommies = [m for m in all_mommies if m != correct_mommy]
            new_opts = random.sample(other_mommies, 3) + [correct_mommy]
            random.shuffle(new_opts)
            st.session_state.current_options = new_opts
            st.rerun()
        else:
            st.error("❌ Oops! Try another Mommy.")

with col2:
    if st.button(options[2], key="opt_2"):
        if options[2] == current["mommy"]:
            st.balloons()
            st.success(f"🎉 Yay! The Mommy of the {current['baby']} is the {options[2]}!")
            st.session_state.match_score += 1
            st.session_state.current_pair = random.choice(ANIMAL_PAIRS)
            all_mommies = [p["mommy"] for p in ANIMAL_PAIRS]
            correct_mommy = st.session_state.current_pair["mommy"]
            other_mommies = [m for m in all_mommies if m != correct_mommy]
            new_opts = random.sample(other_mommies, 3) + [correct_mommy]
            random.shuffle(new_opts)
            st.session_state.current_options = new_opts
            st.rerun()
        else:
            st.error("❌ Oops! Try another Mommy.")

    if st.button(options[3], key="opt_3"):
        if options[3] == current["mommy"]:
            st.balloons()
            st.success(f"🎉 Yay! The Mommy of the {current['baby']} is the {options[3]}!")
            st.session_state.match_score += 1
            st.session_state.current_pair = random.choice(ANIMAL_PAIRS)
            all_mommies = [p["mommy"] for p in ANIMAL_PAIRS]
            correct_mommy = st.session_state.current_pair["mommy"]
            other_mommies = [m for m in all_mommies if m != correct_mommy]
            new_opts = random.sample(other_mommies, 3) + [correct_mommy]
            random.shuffle(new_opts)
            st.session_state.current_options = new_opts
            st.rerun()
        else:
            st.error("❌ Oops! Try another Mommy.")

# Scoreboard & Reset
st.markdown("---")
st.markdown(f"<h3 style='text-align: center;'>🏆 Correct Matches Score: {st.session_state.match_score}</h3>", unsafe_allow_html=True)

col_r1, col_r2, col_r3 = st.columns([1, 2, 1])
with col_r2:
    if st.button("🔄 Reset Score"):
        st.session_state.match_score = 0
        st.rerun()

# --- FOOTER ---
st.markdown("---")
st.markdown(
    "<p style='text-align: center; color: gray;'>Made with ❤️ for Toddler Fun | Streamlit Touch Arcade</p>",
    unsafe_allow_html=True,
)
