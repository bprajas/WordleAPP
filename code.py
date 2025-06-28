import streamlit as st
import itertools
import requests
import numpy as np
import pandas as pd

@st.cache_data

def load_wordle_data():
    url = "https://web.archive.org/web/20220101000805js_/https://www.powerlanguage.co.uk/wordle/main.db1931a8.js"
    response = requests.get(url)
    data = response.text
    wordle_answers = data.split("var Aa=[")[-1].split("]")[0].replace('"', "").upper().split(",")
    valid_entries = data.split(",La=[")[-1].split("]")[0].replace('"', "").upper().split(",")
    valid_entries = sorted(list(set(wordle_answers + valid_entries)))
    wordle_answers = sorted(wordle_answers)
    return wordle_answers, valid_entries

def indices(arr, value):
    return [ind for ind, x in enumerate(arr) if x == value]

def color_sequence(guess, answer, emoji=True):
    guess = list(guess)
    answer = list(answer)
    colors = ["W"] * len(answer)
    for ind, (g, a) in enumerate(zip(guess, answer)):
        if g == a:
            colors[ind] = "G"
            guess[ind] = ""
            answer[ind] = ""
    for ind, (g, a) in enumerate(zip(guess, answer)):
        if g != a and g in answer and g != "":
            g_indices = indices(guess, g)
            a_indices = indices(answer, g)
            if not any(i in g_indices for i in a_indices):
                colors[ind] = "Y"
                answer[answer.index(g)] = ""
    colors = "".join(colors)
    if emoji:
        colors = colors.replace("G", "🟩").replace("Y", "🟨").replace("W", "⬜")
    return colors

def get_words_using_sequence(input_word, sequence, word_list):
    return [word for word in word_list if color_sequence(input_word, word) == sequence]

def count_of_combos(guess, answers, probability=True):
    results = {}
    increment = 1 / len(answers) if probability else 1
    for ans in answers:
        seq = color_sequence(guess, ans)
        results[seq] = results.get(seq, 0) + increment
    return results

def entropy_from_combos(combos):
    return sum(p * (-np.log2(p)) for p in combos.values())

def entropy_df(input_words, possible_answers):
    data = []
    for word in input_words:
        combos = count_of_combos(word, possible_answers)
        entropy = entropy_from_combos(combos)
        data.append((word, entropy))
    df = pd.DataFrame(data, columns=["WORD", "ENTROPY"])
    df = df.sort_values("ENTROPY", ascending=False).set_index("WORD")
    return df

# Streamlit UI
st.title("Wordle Entropy Maximizer")

wordle_answers, valid_words = load_wordle_data()

st.markdown("Enter your previous guesses and their results in the format:")
st.code("CRANE:GYWGW, SLATE:WWGGW")

user_input = st.text_input("Input your guesses and feedback", "")

if user_input:
    try:
        current_list = wordle_answers
        guess_pattern_pairs = [pair.strip().split(":") for pair in user_input.split(",") if ":" in pair]
        for guess, pattern in guess_pattern_pairs:
            guess = guess.strip().upper()
            pattern = pattern.strip().upper().replace("G", "🟩").replace("Y", "🟨").replace("W", "⬜")
            current_list = get_words_using_sequence(guess, pattern, current_list)

        df_entropy = entropy_df(current_list, wordle_answers)
        st.subheader("Top 15 Words by Entropy")
        st.dataframe(df_entropy.head(15))
    except Exception as e:
        st.error(f"There was an error parsing your input: {e}")
