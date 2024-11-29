import json
import sys
import streamlit as st
import subprocess
import re
from io import BytesIO
from fpdf import FPDF

# Set page and theme info
st.set_page_config(
    page_title="QuizCraft - AI Generated Quizzes 🧠📚❓",
    page_icon="📝",
    layout="centered",
    initial_sidebar_state="collapsed",
    menu_items=None
)

# markdown attributes
st.html("""<style> [alt=Logo] { height: 10rem; } </style>""")
st.logo(image="images/logo/quiz-craft-logo.png", size="large")

# App title
st.title("QuizCraft 🧠📚❓")

# Loading json file
with open("response.json", "r") as file:
    RESPONSE_JSON = json.load(file)

# Description
description = st.text("QuizCraft is an AI-powered tool that generates different questions from text.\n"
                     "Simply input some text or upload a PDF/text file, and adjust some parameters.\n"
                     "QuizCraft will generate a quiz for you in seconds! 🚀"
                     )

# Init session state
if "quiz_generated" not in st.session_state:
    st.session_state.quiz_generated = False

if "quiz_data" not in st.session_state:
    st.session_state.quiz_data = None

# Create form
with st.form("user_inputs"):
    # Text input, keep max_chars at 3500 to avoid overflow with the model
    user_prompt = st.text_area("Text Input", height=200, max_chars=3500, help="Enter your text here")

    st.write("<center>OR</center>", unsafe_allow_html=True)

    # File upload
    uploaded_file = st.file_uploader("Upload your TXT or PDF file here",
                                     type=["txt", "pdf"], help="Upload a TXT or PDF file")

    st.divider()

    # User will be able to select the number of questions for each type
    # Based on what available question types were selected above
    # #input fields
    # mcq_count=st.number_input("No. of MCQs: ", min_value=3, max_value=50, placeholder= "10")

    col1, col2, = st.columns(2, gap="large")

    with col1:
        # Question type
        question_types = st.multiselect("Question Types", ["Multiple Choice", "True/False", "Fill in the Blanks"],
                                        default=["Multiple Choice"],
                                        help="Select the type of questions you want in the quiz"
                                        )

    with col2:
        # Quiz difficulty
        options = ["Easy", "Medium", "Hard"]
        difficulty_level = st.segmented_control(
            "Quiz Difficulty", options, default="Medium", help="Select the difficulty level of the quiz"
        )

    # Number of questions
    number_of_questions = st.slider("Number of Questions", min_value=5, max_value=50, value=10,
                                    help="Select the number of questions you want in the quiz"
                                    )
    # Status for generating quiz
    submit = st.form_submit_button("Generate Quiz")

# Outside of the form, create the download quiz logic
def generate_quiz(number_of_questions, difficulty_level, user_prompt):
    with st.status("Generating Quiz...", expanded=True) as status:
        st.write("Running through LLM...")
        quiz_data = run_generate_quiz_script(number_of_questions, difficulty_level, user_prompt)
        if quiz_data:
            st.write("Writing ")
            status.update(
                label="Quiz Generated!", state="complete", expanded=False
            )
            st.toast('Quiz Ready!', icon='🎉')
            st.session_state.quiz_generated = True
            st.session_state.quiz_data = quiz_data  # Store the quiz data in session state

            try:
                json.dumps(quiz_data)  # This will raise an exception if not serializable
                st.session_state.quiz_data = quiz_data
            except TypeError as e:
                print(f"Quiz data is not serializable: {e}")
            
        else:
            st.write("Failed to generate quiz. Please try again.")

# Function to run the generate_quiz_from_prompt.py script
def run_generate_quiz_script(number_of_questions, difficulty_level, user_prompt):
    print(f"Running generate_quiz_from_prompt.py with arguments: {number_of_questions}, {difficulty_level}, {user_prompt}")
    
    # Running the subprocess to generate the quiz
    result = subprocess.run([sys.executable, 'generate_quiz_from_prompt.py',
                             str(number_of_questions), difficulty_level, user_prompt],
                             capture_output=True, text=True)

    print(f"Raw result.stdout: {repr(result.stdout)}")  # Print the raw result stdout for debugging with hidden characters

    # Clean up result.stdout: Strip unnecessary whitespace and newlines
    cleaned_stdout = result.stdout.strip()

    # Regex to extract the JSON block starting with '{' and ending with '}'
    match = re.search(r'(\{.*\})', cleaned_stdout, re.DOTALL)  # re.DOTALL allows '.' to match newlines
    if match:
        json_data = match.group(1)
        print(f"Cleaned JSON data: {repr(json_data)}")  # Debugging the extracted JSON data

        # Try parsing the extracted JSON
        try:
            quiz_data = json.loads(json_data)  # Parse the JSON to get the quiz data
            print(f"Parsed quiz data successfully: {quiz_data}")

        except json.JSONDecodeError as e:
            print(f"JSONDecodeError: {e}")
            quiz_data = None
    else:
        print("No valid JSON response found in stdout.")
        quiz_data = None

    return quiz_data

# Function to convert the quiz data into human-readable format
def format_quiz_as_text(quiz_data):
    formatted_quiz = ""
    question_number = 1
    
    # Process each quiz question
    for quiz in quiz_data.get("quiz", []):
        formatted_quiz += f"{question_number}. {quiz['question']}\n"
        options = quiz.get('options', [])
        
        # Format options as 'a.', 'b.', 'c.', 'd.'
        for idx, option in enumerate(options, 1):
            formatted_quiz += f"   {chr(96 + idx)}. {option}\n"
        formatted_quiz += "\n"
        question_number += 1

    # Build the answer key
    formatted_quiz += "\nAnswer Key:\n"
    question_number = 1
    for quiz in quiz_data.get("quiz", []):
        options = quiz.get('options', [])
        correct_answer = quiz.get('answer', "")
        
        # Find the correct option letter (e.g., 'a', 'b', 'c', 'd') for the answer
        correct_index = options.index(correct_answer)  # Find the index of the correct answer in options
        correct_letter = chr(97 + correct_index)  # Convert to letter ('a', 'b', 'c', etc.)
        
        # Format the answer key entry
        formatted_quiz += f"{question_number}. ({correct_letter}) - {correct_answer}\n"
        question_number += 1
    
    return formatted_quiz

# Generate quiz if submit button is clicked
if submit:
    generate_quiz(number_of_questions, difficulty_level, user_prompt)

# Function to generate a PDF file for the quiz
def generate_quiz_pdf(quiz_text):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    # Split the formatted quiz text into lines and write to the PDF
    for line in quiz_text.split("\n"):
        pdf.multi_cell(0, 10, line)

    # Return the PDF content as bytes
    return pdf.output(dest='S').encode('latin1')

# Download quiz button
if st.session_state.quiz_generated:
    formatted_quiz = format_quiz_as_text(st.session_state.quiz_data)  # Format the quiz into a readable text

    # Generate PDF content
    pdf_content = generate_quiz_pdf(formatted_quiz)

    pdf_download, text_download, = st.columns(2, vertical_alignment="bottom")

    with pdf_download:
        st.download_button(
            use_container_width=True,
            label="Download Quiz (.PDF) 📃",
            key="download_pdf",
            data=pdf_content,
            file_name="quiz.pdf",
            mime="application/pdf"
        )

    with text_download:
        # Text download button
        st.download_button(
            use_container_width=True,
            label="Download Quiz (.TXT) 📜",
            key="download_txt",
            data=formatted_quiz,
            file_name="quiz.txt",
            mime="text/plain"
        )

    # debug to write out the quiz data without downloading it
    # Optionally display the formatted quiz
    # st.write(formatted_quiz)