import random
import streamlit as st

# --- PAGE CONFIGURATION (WIDE LAYOUT) ---
st.set_page_config(
    page_title="Aahana's Play Zone", page_icon="🌟", layout="wide"
)

# --- CUSTOM CSS FOR BIGGER, TODDLER-FRIENDLY BUTTONS & WIDER SCREEN ---
st.markdown(
    """
    <style>
    .stButton>button {
        font-size: 24px !important;
        padding: 24px !important;
        border-radius: 20px !important;
        font-weight: bold;
        width: 100%;
        box-shadow: 0px 4px 6px rgba(0,0,0,0.1);
    }
    .big-title {
        font-size: 3em !important;
        text-align: center;
        color: #FF4B4B;
        font-weight: bold;
    }
    .instruction-text {
        font-size: 1.5em !important;
        text-align: center;
        color: #555;
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
        "<h2 style='text-align: center;'>🔐 Parent Login to Aahana's Play Zone</h2>",
        unsafe_allow_html=True,
    )
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            entered_password = st.text_input(
                "Enter Password (default: admin)", type="password"
            )
            submit_btn = st.form_submit_button("Enter Play Zone")
            if submit_btn:
                if entered_password == APP_PASSWORD:
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("Incorrect password. Try again.")
    st.stop()  # Stop execution until authenticated

# --- MAIN TODDLER APP ---
st.markdown(
    "<h1 class='big-title'>🌟 Aahana's Interactive Play Zone 🌟</h1>",
    unsafe_allow_html=True,
)
st.markdown(
    "<p class='instruction-text'>Pick a game tab below and have fun!</p>",
    unsafe_allow_html=True,
)

# Create 5 Interactive Tabs (Including Animal Match!)
tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["🎈 Magic Balloon Pop", "🍎 Fruit Counting", "🐾 Mommy & Baby Match", "🦁 Animal Sound Box", "🎨 Color Matcher"]
)

# ==========================================
# TAB 1: MAGIC BALLOON POP
# ==========================================
with tab1:
    st.header("🎈 Magic Balloon Pop")
    st.write("Tap the colorful balloons below to pop them and watch the counter grow!")

    if "balloon_score" not in st.session_state:
        st.session_state.balloon_score = 0

    col1, col2, col3, col4, col5 = st.columns(5)
    balloons = [
        ("🔴 Red", "pop_red"),
        ("🔵 Blue", "pop_blue"),
        ("🟢 Green", "pop_green"),
        ("🟡 Yellow", "pop_yellow"),
        ("🟣 Purple", "pop_purple"),
    ]

    for idx, (b_label, b_key) in enumerate(balloons):
        with [col1, col2, col3, col4, col5][idx]:
            if st.button(b_label, key=b_key, use_container_width=True):
                st.balloons()
                st.session_state.balloon_score += 1
                st.success(f"Pop! 🎉 ({b_label})")

    st.markdown(f"### 🏆 Total Pops: **{st.session_state.balloon_score}**")

    if st.button("🔄 Reset Balloons"):
        st.session_state.balloon_score = 0
        st.rerun()

# ==========================================
# TAB 2: FRUIT COUNTING
# ==========================================
with tab2:
    st.header("🍎 Fruit Counting Adventure")
    st.write("Count the fruits on the screen and tap the correct number!")

    if "target_count" not in st.session_state:
        st.session_state.target_count = random.randint(1, 5)
        st.session_state.fruit_score = 0

    target = st.session_state.target_count
    fruit_icon = random.choice(["🍎", "🍌", "🍓", "🍊", "🍇"])

    st.markdown(
        f"<h2 style='text-align: center; background-color: #f0f2f6; padding: 20px; border-radius: 10px;'>{fruit_icon * target}</h2>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='text-align: center; font-weight: bold;'>How many fruits do you see?</p>",
        unsafe_allow_html=True,
    )

    btn_cols = st.columns(5)
    for i in range(1, 6):
        with btn_cols[i - 1]:
            if st.button(str(i), key=f"count_{i}", use_container_width=True):
                if i == target:
                    st.balloons()
                    st.success(
                        f"🌟 Correct! There are {target} {fruit_icon} fruits!"
                    )
                    st.session_state.fruit_score += 1
                    st.session_state.target_count = random.randint(1, 5)
                    st.rerun()
                else:
                    st.error("❌ Not quite! Try counting again.")

    st.markdown(f"**Score:** {st.session_state.fruit_score} 🎯")

# ==========================================
# TAB 3: MOMMY & BABY ANIMAL MATCH (10 Animals)
# ==========================================
with tab3:
    st.header("🐾 Mommy & Baby Animal Match")
    st.write("Find the right Mommy animal for the cute baby!")

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

    if "animal_score" not in st.session_state:
        st.session_state.animal_score = 0
    if "current_pair" not in st.session_state:
        st.session_state.current_pair = random.choice(ANIMAL_PAIRS)
        all_mommies = [p["mommy"] for p in ANIMAL_PAIRS]
        correct_m = st.session_state.current_pair["mommy"]
        other_m = [m for m in all_mommies if m != correct_m]
        st.session_state.animal_options = random.sample(other_m, 3) + [correct_m]
        random.shuffle(st.session_state.animal_options)

    current_a = st.session_state.current_pair

    st.markdown(
        f"<div style='text-align: center; padding: 25px; background-color: #e8f5e9; border-radius: 15px; margin-bottom: 20px;'>"
        f"<h2>Baby: <b>{current_a['baby']}</b></h2>"
        f"<h3>Who is the Mommy? 🤔</h3>"
        f"</div>",
        unsafe_allow_html=True,
    )

    opts = st.session_state.animal_options
    col_m1, col_m2 = st.columns(2)

    for idx, opt in enumerate(opts):
        target_col = col_m1 if idx < 2 else col_m2
        with target_col:
            if st.button(opt, key=f"mommy_opt_{idx}", use_container_width=True):
                if opt == current_a["mommy"]:
                    st.balloons()
                    st.success(f"🎉 Yay! The Mommy of the {current_a['baby']} is the {opt}!")
                    st.session_state.animal_score += 1
                    st.session_state.current_pair = random.choice(ANIMAL_PAIRS)
                    all_mommies = [p["mommy"] for p in ANIMAL_PAIRS]
                    correct_m = st.session_state.current_pair["mommy"]
                    other_m = [m for m in all_mommies if m != correct_m]
                    new_opts = random.sample(other_m, 3) + [correct_m]
                    random.shuffle(new_opts)
                    st.session_state.animal_options = new_opts
                    st.rerun()
                else:
                    st.error("❌ Oops! Try another Mommy.")

    st.markdown(f"### 🏆 Animal Match Score: {st.session_state.animal_score}")

# ==========================================
# TAB 4: ANIMAL SOUND BOX
# ==========================================
with tab4:
    st.header("🦁 Animal Sound Box")
    st.write("Tap your favorite animal to hear what they say!")

    animal_cols = st.columns(4)
    animals = [
        {"name": "Lion", "emoji": "🦁", "sound": "Roar! 🦖"},
        {"name": "Cow", "emoji": "🐮", "sound": "Moo! 🥛"},
        {"name": "Duck", "emoji": "🦆", "sound": "Quack Quack! 🌊"},
        {"name": "Dog", "emoji": "🐶", "sound": "Woof Woof! 🦴"},
    ]

    for idx, animal in enumerate(animals):
        with animal_cols[idx]:
            if st.button(
                f"{animal['emoji']}\n{animal['name']}",
                key=f"animal_{idx}",
                use_container_width=True,
            ):
                st.snow()
                st.markdown(
                    f"<div style='text-align: center; padding: 15px; background-color: #e6f4ea; border-radius: 10px;'>"
                    f"<h2>{animal['emoji']} The {animal['name']}</h2>"
                    f"<h3>Says: <b>{animal['sound']}</b></h3>"
                    f"</div>",
                    unsafe_allow_html=True,
                )

# ==========================================
# TAB 5: COLOR MATCHER
# ==========================================
with tab5:
    st.header("🎨 Color Matching Challenge")
    st.write("Find and click the matching color name!")

    if "color_target" not in st.session_state:
        st.session_state.color_target = random.choice(
            ["Red", "Blue", "Green", "Yellow"]
        )
        st.session_state.color_score = 0

    c_target = st.session_state.color_target
    st.markdown(
        f"<h3 style='text-align: center;'>Can you find the box for: <span style='color: #ff4b4b; font-size: 1.2em;'>{c_target}</span>?</h3>",
        unsafe_allow_html=True,
    )

    cc1, cc2, cc3, cc4 = st.columns(4)
    colors_list = [
        ("🔴 Red", "Red", cc1),
        ("🔵 Blue", "Blue", cc2),
        ("🟢 Green", "Green", cc3),
        ("🟡 Yellow", "Yellow", cc4),
    ]

    for label, col_name, col_obj in colors_list:
        with col_obj:
            if st.button(label, key=f"col_btn_{col_name}", use_container_width=True):
                if col_name == c_target:
                    st.balloons()
                    st.success("🎉 Awesome job matching the color!")
                    st.session_state.color_score += 1
                    st.session_state.color_target = random.choice(
                        ["Red", "Blue", "Green", "Yellow"]
                    )
                    st.rerun()
                else:
                    st.error("Oops! Try another color.")

    st.markdown(f"**Score:** {st.session_state.color_score} 🌈")

# --- FOOTER ---
st.markdown("---")
st.markdown(
    "<p style='text-align: center; color: gray;'>Made with ❤️ for Aahana | Streamlit Interactive Play Zone</p>",
    unsafe_allow_html=True,
)
