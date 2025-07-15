import streamlit as st
import json
import re
from typing import List, Dict

def initialize_session_state():
    if 'questions' not in st.session_state:
        st.session_state.questions = []
    if 'current_question_index' not in st.session_state:
        st.session_state.current_question_index = 0
    if 'user_answers' not in st.session_state:
        st.session_state.user_answers = {}
    if 'quiz_started' not in st.session_state:
        st.session_state.quiz_started = False
    if 'quiz_completed' not in st.session_state:
        st.session_state.quiz_completed = False
    if 'submitted' not in st.session_state:
        st.session_state.submitted = False

def parse_questions(text: str) -> List[Dict]:
    questions = []
    current_question = None
    current_options = []
    correct_answer = None

    for line in text.split('\n'):
        line = line.strip()
        if not line:
            continue

        if re.match(r"^\d+[\.\)]|^(Q|Question)\s*[:\d]", line, re.IGNORECASE):
            if current_question and current_options and correct_answer:
                questions.append({
                    "question": current_question,
                    "options": [opt[0] for opt in current_options],
                    "correct_answer": correct_answer
                })
            current_question = re.sub(r"^(Q(uestion)?[:\s]*\d*\.?)|\d+[\.\)]", "", line, flags=re.IGNORECASE).strip()
            current_options = []
            correct_answer = None

        elif re.match(r"^[a-d1-4A-D]\)", line):
            option_text = line[2:].strip()
            is_correct = bool(re.search(r'\*|\[CORRECT\]|\✓', option_text, re.IGNORECASE))
            clean_text = re.sub(r'\*|\[CORRECT\]|\✓', '', option_text).strip()
            current_options.append((clean_text, is_correct))
            if is_correct:
                correct_answer = clean_text

    if current_question and current_options and correct_answer:
        questions.append({
            "question": current_question,
            "options": [opt[0] for opt in current_options],
            "correct_answer": correct_answer
        })

    return questions

def add_questions_from_text(text: str):
    questions = parse_questions(text)
    if not questions:
        st.warning("No valid questions with correct answers found.")
        return False
    st.session_state.questions.extend(questions)
    return True

def display_question(question_data: Dict, question_num: int):
    st.subheader(f"Question {question_num + 1}")
    st.write(question_data["question"])

    key_prefix = f"q_{question_num}"
    user_answer_key = f"{key_prefix}_user_answer"
    submitted_key = f"{key_prefix}_submitted"

    if submitted_key not in st.session_state:
        st.session_state[submitted_key] = False

    if not st.session_state[submitted_key]:
        selected_option = st.radio(
            "Select your answer:",
            options=question_data["options"],
            index=None,
            key=user_answer_key
        )

        if selected_option is not None:
            if st.button("✅ Submit Answer", key=f"{key_prefix}_submit"):
                st.session_state.submitted = True
                st.session_state[submitted_key] = True
                st.session_state.user_answers[question_num] = selected_option
                st.rerun()
    else:
        user_ans = st.session_state.user_answers.get(question_num)
        correct_ans = question_data["correct_answer"]

        for opt in question_data["options"]:
            if opt == user_ans and opt == correct_ans:
                st.success(f"✅ {opt}")
            elif opt == user_ans and opt != correct_ans:
                st.error(f"❌ {opt}")
            elif opt == correct_ans:
                st.success(f"✅ {opt}")
            else:
                st.write(opt)

        st.info("Click 'Next' to continue.")


def calculate_score():
    score = 0
    for i, question in enumerate(st.session_state.questions):
        if st.session_state.user_answers.get(i) == question["correct_answer"]:
            score += 1
    return score

def reset_quiz():
    st.session_state.quiz_started = False
    st.session_state.quiz_completed = False
    st.session_state.current_question_index = 0
    st.session_state.user_answers = {}
    st.session_state.submitted = False
    # Reset per-question submission flags
    for i in range(len(st.session_state.questions)):
        st.session_state[f"q_{i}_submitted"] = False

def main():
    st.title("📚 Quiz Generator & Player")
    initialize_session_state()

    with st.sidebar:
        st.header("🛠️ Quiz Creator")
        question_text = st.text_area(
            "Enter your questions:",
            height=300,
            help="""Use one of these formats:
1. What is 2+2?
a) 3
b) 4 [CORRECT]
c) 5

Q: Capital of France?
a) London
b) Paris *
c) Berlin

Question 3: Which is a fruit?
1) Apple ✓
2) Carrot
3) Potato"""
        )

        if st.button("➕ Add Questions"):
            if add_questions_from_text(question_text):
                st.success(f"Added {len(st.session_state.questions)} question(s)!")
                st.rerun()

        if st.session_state.questions:
            st.download_button(
                label="⬇️ Export Questions",
                data=json.dumps(st.session_state.questions, indent=2),
                file_name="quiz_questions.json",
                mime="application/json"
            )

            uploaded_file = st.file_uploader("📤 Import Quiz (JSON)", type="json")
            if uploaded_file:
                try:
                    data = json.load(uploaded_file)
                    st.session_state.questions.extend(data)
                    st.success(f"Imported {len(data)} question(s)!")
                    st.rerun()
                except json.JSONDecodeError:
                    st.error("Invalid JSON format.")

            if st.button("🗑 Clear All Questions"):
                st.session_state.questions = []
                reset_quiz()
                st.rerun()

    if not st.session_state.questions:
        st.info("Add questions to begin the quiz.")
        return

    if not st.session_state.quiz_started:
        st.header("📝 Quiz Preview")
        st.write(f"Total questions: **{len(st.session_state.questions)}**")

        if st.button("🚀 Start Quiz"):
            st.session_state.quiz_started = True
            st.rerun()

        st.subheader("Preview of Questions")
        for i, q in enumerate(st.session_state.questions):
            st.markdown(f"**{i+1}. {q['question']}**")
            st.write(f"Options: {', '.join(q['options'])}")
            st.write(f"✅ Correct: {q['correct_answer']}")
            st.write("---")
    else:
        if st.session_state.current_question_index < len(st.session_state.questions):
            current_question = st.session_state.questions[st.session_state.current_question_index]
            display_question(current_question, st.session_state.current_question_index)

            submitted_key = f"q_{st.session_state.current_question_index}_submitted"
            col1, col2 = st.columns(2)
            if st.session_state.current_question_index > 0:
                if col1.button("⬅ Previous"):
                    st.session_state.current_question_index -= 1
                    st.rerun()

            if st.session_state.get(submitted_key, False):
                if st.session_state.current_question_index < len(st.session_state.questions) - 1:
                    if col2.button("Next ➡"):
                        st.session_state.current_question_index += 1
                        st.rerun()
                else:
                    if col2.button("✅ Finish Quiz"):
                        st.session_state.quiz_completed = True
                        st.rerun()
        else:
            st.session_state.quiz_completed = True

    if st.session_state.quiz_completed:
        st.header("📊 Quiz Results")
        score = calculate_score()
        total = len(st.session_state.questions)
        st.success(f"🎉 You scored **{score}/{total}** ({score / total * 100:.1f}%)")

        st.subheader("🧐 Answer Review")
        for i, q in enumerate(st.session_state.questions):
            user_answer = st.session_state.user_answers.get(i, "Not answered")
            correct = user_answer == q["correct_answer"]
            st.markdown(f"**Q{i+1}:** {q['question']}")
            st.write(f"- Your answer: `{user_answer}` {'✅' if correct else '❌'}")
            if not correct:
                st.write(f"- Correct answer: `{q['correct_answer']}`")
            st.write("---")

        if st.button("🔁 Retake Quiz"):
            reset_quiz()
            st.rerun()

if __name__ == "__main__":
    main()
