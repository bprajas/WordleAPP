import streamlit as st
import itertools
import numpy as np
import pandas as pd

# ---------------------------- DATA LOADER ---------------------------- #

@st.cache_data
def load_wordle_data():
    with open("wordle_data.js", "r") as f:
        data = f.read()

    wordle_answers = data.split("var Aa=[")[-1].split("]")[0].replace('"', "").upper().split(",")
    valid_entries = data.split(",La=[")[-1].split("]")[0].replace('"', "").upper().split(",")
    full_word_list = sorted(list(set(wordle_answers + valid_entries)))
    return sorted(wordle_answers), full_word_list

# ---------------------------- WORDLE ENGINE ---------------------------- #

def indices(arr, value):
    return [i for i, x in enumerate(arr) if x == value]

def color_sequence(guess, answer, emoji=True):
    guess, answer = list(guess), list(answer)
    result = ["W"] * len(answer)

    for i in range(len(answer)):
        if guess[i] == answer[i]:
            result[i] = "G"
            guess[i] = answer[i] = ""

    for i in range(len(answer)):
        if guess[i] and guess[i] in answer:
            result[i] = "Y"
            answer[answer.index(guess[i])] = ""

    code = "".join(result)
    return code.replace("G", "🟩").replace("Y", "🟨").replace("W", "⬜") if emoji else code

def get_words_using_sequence(guess, sequence, words):
    return [word for word in words if color_sequence(guess, word) == sequence]

def count_combos(guess, answers):
    results = {}
    for ans in answers:
        seq = color_sequence(guess, ans)
        results[seq] = results.get(seq, 0) + 1 / len(answers)
    return results

def entropy(combos):
    return sum(p * (-np.log2(p)) for p in combos.values())

def entropy_df(possible_guesses, possible_answers):
    data = []
    for word in possible_guesses:
        combos = count_combos(word, possible_answers)
        e = entropy(combos)
        data.append((word, e))
    df = pd.DataFrame(data, columns=["WORD", "ENTROPY"]).sort_values("ENTROPY", ascending=False)
    return df.set_index("WORD")

# ---------------------------- STREAMLIT APP ---------------------------- #

st.set_page_config(page_title="Wordle Helper", layout="centered")

st.markdown("""
    <style>
    html, body, [class*="css"] {
        font-family: 'Segoe UI', sans-serif;
        font-size: 16px;
    }
    .main {
        background-color: #f9f9f9;
    }
    .block-container {
        padding-top: 2rem;
        padding-left: 1rem;
        padding-right: 1rem;
    }
    @media (max-width: 600px) {
        .block-container {
            padding-left: 0.5rem;
            padding-right: 0.5rem;
        }
    }
    textarea {
        font-family: monospace;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🧠 ENTROPY MAXIMISED WORDLE SOLVER")
st.write("This tool recommends the most informative next guess based on Wordle feedback.")

answers, all_words = load_wordle_data()

with st.expander("📘 How to Use (Tap to Expand)", expanded=True):
    st.markdown("""
    Enter previous guesses with feedback as:
    ```
    CRANE:GYWGW, SLATE:WWGGW
    ```
    - G = 🟩 Green = Correct letter & position  
    - Y = 🟨 Yellow = Correct letter, wrong position  
    - W = ⬜ White = Letter not in word
    """)

user_input = st.text_area("✍️ Enter guesses and feedback:", height=140, placeholder="CRANE:GYWGW, SLATE:WWGGW")

if user_input:
    try:
        filtered_words = answers.copy()
        entries = [pair.strip().split(":") for pair in user_input.split(",") if ":" in pair]

        for guess, pattern in entries:
            guess = guess.strip().upper()
            pattern = pattern.strip().upper().replace("G", "🟩").replace("Y", "🟨").replace("W", "⬜")
            filtered_words = get_words_using_sequence(guess, pattern, filtered_words)

        df = entropy_df(all_words, filtered_words)
        st.success(f"✅ {len(filtered_words)} possible words remaining.")
        st.subheader("🔝 Top 15 Next Guesses")
        st.dataframe(df.head(15), use_container_width=True)

    except Exception as e:
        st.error(f"⚠️ Something went wrong: {e}")
else:
    st.info("Input guesses above to get recommendations.")
