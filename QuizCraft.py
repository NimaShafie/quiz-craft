import json
import sys
import streamlit as st
import subprocess

# set page and theme info
st.set_page_config(
    page_title="QuizCraft - AI Generated Quizzes 🧠📚❓",
    page_icon="📝",
    layout="centered",
    initial_sidebar_state="collapsed",
    menu_items=None
    )

# logo attributes
st.html("""<style> [alt=Logo] { height: 10rem; } </style>""")
st.logo(image="images/logo/quiz-craft-logo.png", size="large")

# app title
st.title("QuizCraft 🧠📚❓")

# importing necessary packages from LangChain
# from langchain_community.chat_models import ChatOpenAI
# from langchain.prompts import PromptTemplate
# from langchain.chains import LLMChain
# from langchain.chains import SequentialChain

# loading json file
with open("response.json", "r") as file:
    RESPONSE_JSON = json.load(file)

# description
description = st.text("QuizCraft is an AI-powered tool that generates different questions from text.\n"
                     "Simply input some text or upload a PDF/text file, and adjust some parameters.\n"
                     "QuizCraft will generate a quiz for you in seconds! 🚀"
                     )

# create form
with st.form("user_inputs"):
    # text input, keep max_chars at 3500 to avoid overflow with the model
    user_prompt = st.text_area("Text Input", height=200, max_chars=3500, help="Enter your text here")

    st.write("<center>OR</center>", unsafe_allow_html=True)

    # file upload
    uploaded_file = st.file_uploader("Upload your TXT or PDF file here",
                                     type=["txt", "pdf"], help="Upload a TXT or PDF file")

    st.divider()

    # probably not needed
    # #subject
    # subject = st.text_input("Subject name:", max_chars=20, placeholder="Machine Learning")

    # user will be able to select the number of questions for each type
    # based on what available question types were selected above
    # #input fields
    # mcq_count=st.number_input("No. of MCQs: ", min_value=3, max_value=50, placeholder= "10")

    col1, col2, = st.columns(2, gap="large")

    with col1:
        #question type
        question_types = st.multiselect("Question Types", ["Multiple Choice", "True/False", "Fill in the Blanks"],
                                        default=["Multiple Choice"],
                                        help="Select the type of questions you want in the quiz"
                                        )

    with col2:
        #quiz difficulty
        options = ["Easy", "Medium", "Hard"]
        difficulty_level = st.segmented_control(
            "Quiz Difficulty", options, default="Medium", help="Select the difficulty level of the quiz"
        )

    #number of questions
    number_of_questions = st.slider("Number of Questions", min_value=5, max_value=50, value=10,
                                    help="Select the number of questions you want in the quiz"
                                    )
    
    # status for generating quiz
    submit = st.form_submit_button("Generate Quiz")

# outside of the form, create the download quiz logic
def generate_quiz(number_of_questions, difficulty_level, user_prompt):
    with st.status("Generating Quiz...", expanded=True) as status:
        st.write("Running through LLM...")
        quiz_data = run_generate_quiz_script(number_of_questions, difficulty_level, user_prompt)
        if quiz_data:
            status.update(
                label="Quiz Generated!", state="complete", expanded=False
            )
            st.toast('Quiz Ready!', icon='🎉')
            st.session_state.quiz_generated = True
            st.session_state.quiz_data = quiz_data  # Store the quiz data in session state
        else:
            st.write("Failed to generate quiz. Please try again.")


# previous version
# # outside of the form, create the download quiz logic
# def generate_quiz(number_of_questions, difficulty_level, user_prompt):
#     with st.status("Generating Quiz...", expanded=True) as status:
#         st.write("Running through LLM...")
#         quiz_data = run_generate_quiz_script(number_of_questions, difficulty_level, user_prompt)
#         if quiz_data:
#             status.update(
#                 label="Quiz Generated!", state="complete", expanded=False
#             )
#             st.write("------LOG------")
#             st.write(quiz_data)
#             st.toast('Quiz Ready!', icon='🎉')
#             st.session_state.quiz_generated = True
#         else:
#             st.write("Failed to generate quiz. Please try again.")

def run_generate_quiz_script(number_of_questions, difficulty_level, user_prompt):
    print(f"Running generate_quiz_from_prompt.py with arguments: {number_of_questions}, {difficulty_level}, {user_prompt}")
    result = subprocess.run([sys.executable, 'generate_quiz_from_prompt.py',
                             str(number_of_questions), difficulty_level, user_prompt],
                             capture_output=True, text=True)
    # print(f"Printing result.stdout results: {result.stdout}")
    # print(f"Script stdout: {result.stdout}")
    # print(f"Script stderr: {result.stderr}")
    # print(f"Return code: {result.returncode}")
    # print(f"Type of result.stdout: {type(result.stdout)}")
    quiz_data = result.stdout
    try:
        print(f"Trying to parse JSON...")
        print(f"result.stdout: ", result.stdout)
    except json.JSONDecodeError as e:
        print(f"JSONDecodeError: {e}")
        quiz_data = None
    return quiz_data

if st.session_state.get('quiz_generated', False):
    st.write("st.session_state.get('quiz_generated', False): ON")
    print("st.session_state.get('quiz_generated', False): ON")
    quiz_data = json.dumps(st.session_state.quiz_data, indent=4)  # Convert the JSON object back to a string
    download_button = st.download_button(
        label="Download Quiz",
        data=quiz_data,
        file_name="quiz.txt",
        mime="application/json"
    )
    if download_button:
        st.write("File download initiated.")
        st.write("Part 2: Quiz Data:")
        st.write(quiz_data)

if submit:
    generate_quiz(number_of_questions, difficulty_level, user_prompt)

# if st.session_state.get('quiz_generated', False):
#     download_button = st.download_button(
#         label="Download Quiz",
#         data=quiz_data,
#         file_name="quiz.txt",
#         mime="text/plain"
#     )
#     if download_button:
#         st.write("File download initiated.")
#         st.write("Part 2: Quiz Data:")
#         st.write(quiz_data)