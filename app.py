import random
import streamlit as st

# --- PAGE CONFIGURATION (WIDE LAYOUT) ---
st.set_page_config(
    page_title="Toddler Animal Match Game", page_icon="🐾", layout="wide"
)

# --- CUSTOM CSS FOR LARGE TODDLER TOUCH TARGETS ---
st.markdown(
    """
    <style>
    .stButton>button {
        font-size: 22px !important;
        padding: 22px !important;
        border-radius: 18px !important;
        font-weight: bold;
        width: 100%;
        box-shadow: 0px 4px 6px rgba(0,0,0,0.1);
    }
    .title-text {
        text-align: center;
        color: #d81b60;
        font-size: 2.8em !important;
        font-weight: bold;
    }
    .instruction {
        text-align: center;
        font-size: 1.5em !important;
        color: #333;
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
    {"baby": "Puppy 🐶", "mommy": "Dog 🐕", "id": 1},
    {"baby": "Kitten 🐱", "mommy": "Cat 🐈", "id": 2},
    {"baby": "Calf 🐮", "mommy": "Cow 🐄", "id": 3},
    {"baby": "Chick 🐥", "mommy": "Chicken 🐔", "id": 4},
    {"baby": "Piglet 🐷", "mommy": "Pig 🐖", "id": 5},
    {"baby": "Duckling 🦆", "mommy": "Duck 🦆", "id": 6},
    {"baby": "Foal 🐴", "mommy": "Horse 🐎", "id": 7},
    {"baby": "Lamb 🐑", "mommy": "Sheep 🐏", "id": 8},
    {"baby": "Kid 🐐", "mommy": "Goat 🐐", "id": 9},
    {"baby": "Cub 🦁", "mommy": "Lion 🦁", "id": 10},
]

# Initialize Session State for Active Round
if "score" not in st.session_state:
    st.session_state.score = 0
if "selected_baby" not in st.session_state:
    st.session_state.selected_baby = None
if "round_animals" not in st.session_state:
    # Pick 4 random pairs for the current board
    selected = random.sample(ANIMAL_PAIRS, 4)
    st.session_state.babies_round = selected.copy()
    random.shuffle(st.session_state.babies_round)
    st.session_state.mommies_round = selected.copy()
    random.shuffle(st.session_state.mommies_round)

# --- MAIN APP UI ---
st.markdown(
    "<h1 class='title-text'>🐾 Match Baby to Mommy! 🐾</h1>",
    unsafe_allow_html=True,
)
st.markdown(
    "<p class='instruction'><b>Step 1:</b> Click a Baby Animal on the left. <br><b>Step 2:</b> Click its Mommy on the right to match them!</p>",
    unsafe_allow_html=True,
)
st.markdown("---")

col_left, col_center, col_right = st.columns([2, 1, 2])

# --- LEFT COLUMN: BABY ANIMALS ---
with col_left:
    st.markdown("<h3 style='text-align: center;'>👶 Baby Animals</h3>", unsafe_allow_html=True)
    for animal in st.session_state.babies_round:
        # Highlight if selected
        is_selected = st.session_state.selected_baby == animal["id"]
        btn_label = f"✨ {animal['baby']} ✨" if is_selected else animal["baby"]
        
        if st.button(btn_label, key=f"baby_{animal['id']}"):
            st.session_state.selected_baby = animal["id"]
            st.rerun()

# --- CENTER COLUMN: STATUS & FEEDBACK ---
with col_center:
    st.markdown("<br><br>", unsafe_allow_html=True)
    if st.session_state.selected_baby:
        active_baby = next(a for a in st.session_state.babies_round if a["id"] == st.session_state.selected_baby)
        st.markdown(
            f"<div style='text-align: center; background-color: #fff3cd; padding: 15px; border-radius: 12px; border: 2px dashed orange;'>"
            f"<h4>Selected Baby:</h4>"
            f"<h2>{active_baby['baby']}</h2>"
            f"<p>Now click the matching Mommy! 👉</p>"
            f"</div>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"<div style='text-align: center; background-color: #e2e3e5; padding: 15px; border-radius: 12px;'>"
            f"<h4>Score: 🏆 {st.session_state.score}</h4>"
            f"<p>Tap a baby animal first!</p>"
            f"</div>",
            unsafe_allow_html=True,
        )
    
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔄 New Board"):
        selected = random.sample(ANIMAL_PAIRS, 4)
        st.session_state.babies_round = selected.copy()
        random.shuffle(st.session_state.babies_round)
        st.session_state.mommies_round = selected.copy()
        random.shuffle(st.session_state.mommies_round)
        st.session_state.selected_baby = None
        st.rerun()

# --- RIGHT COLUMN: MOMMY ANIMALS ---
with col_right:
    st.markdown("<h3 style='text-align: center;'>👩‍👧 Mommy Animals</h3>", unsafe_allow_html=True)
    for animal in st.session_state.mommies_round:
        if st.button(animal["mommy"], key=f"mommy_{animal['id']}"):
            if st.session_state.selected_baby is None:
                st.warning("⚠️ Please select a Baby Animal first!")
            else:
                # Check if correct match
                if st.session_state.selected_baby == animal["id"]:
                    st.balloons()
                    st.success(f"🎉 Correct! You matched the {animal['mommy']} with her baby!")
                    st.session_state.score += 1
                    st.session_state.selected_baby = None
                    
                    # Remove matched pair and load next or refresh board if empty
                    st.session_state.babies_round = [a for a in st.session_state.babies_round if a["id"] != animal["id"]]
                    st.session_state.mommies_round = [a for a in st.session_state.mommies_round if a["id"] != animal["id"]]
                    
                    if not st.session_state.babies_round:
                        st.success("🌟 Amazing! You matched all animals on this board!")
                        selected = random.sample(ANIMAL_PAIRS, 4)
                        st.
