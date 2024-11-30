"""
QuizCraft: An AI-powered tool for generating quizzes (Using LLMs and Streamlit).
Created by NS

Usage:

1. Launch the application:
   Run the script in your Streamlit environment to launch the QuizCraft UI.

2. Generate a quiz:
   - Provide input text or upload a file (TXT or PDF).
   - Configure quiz parameters (e.g., number of questions, difficulty level, question types).
   - Click "Generate Quiz" to create a custom quiz.

3. Download the quiz:
   - Download the quiz as a formatted text file (.TXT) or PDF (.PDF) using the provided download buttons.

Parameters:

- `difficulty_level`: <str> The difficulty of the quiz. Options: "Easy", "Medium", "Hard".
- `number_of_questions`: <int> The total number of questions to include in the quiz. Range: 5–50.
- `user_prompt`: <str> Input text used to generate quiz questions. Can be a direct input or extracted from uploaded files.

Dependencies:
- Python libraries: Streamlit, subprocess, re, json, FPDF, ollama, ollama model, ollama_index, llama_index, config_reader
"""
import json
import sys
import streamlit as st
import subprocess
import re
import os
# from io import BytesIO
from fpdf import FPDF

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

# # Validation checks after the user clicks submit
# def validate_user_input(user_input):
#     # Case 1: Both text input and file upload are empty
#     if not user_prompt and not uploaded_file:
#         st.error("Please provide input by entering text or uploading a .TXT or .PDF file.")
    
#     # Case 2: Both text input and file upload are provided
#     elif user_prompt and uploaded_file:
#         st.error("Please use only one input method: either enter text or upload a file.")

#     # Case 3: Only file upload is provided
#     elif uploaded_file:
#         # Save uploaded file temporarily
#         temp_file_path = f"./temp/{uploaded_file.name}"
#         os.makedirs(os.path.dirname(temp_file_path), exist_ok=True)
#         with open(temp_file_path, "wb") as f:
#             f.write(uploaded_file.read())

#         # Call generate_quiz_on_file.py script
#         result = subprocess.run(
#             [
#                 sys.executable,
#                 "generate_quiz_on_file.py",
#                 "--file_path",
#                 temp_file_path,
#                 "--difficulty",
#                 difficulty_level.lower(),
#                 "--number_of_questions",
#                 str(number_of_questions),
#             ],
#             capture_output=True,
#             text=True,
#         )

#         # Handle result
#         if result.returncode == 0:
#             st.success("Quiz Generated Successfully!")
#             try:
#                 quiz_data = json.loads(result.stdout)
#                 st.json(quiz_data)  # Display the quiz as JSON in the UI
#             except json.JSONDecodeError:
#                 st.error("Failed to parse quiz data.")
#         else:
#             st.error("Quiz generation failed. Check the logs.")
#             st.text(result.stderr)

    # # Case 4: Only user input is provided
    # elif user_prompt:
    #     generate_quiz(number_of_questions, difficulty_level, user_prompt)

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

# if "quiz_data" not in st.session_state:
#     st.session_state.quiz_data = None

# # Initialize Streamlit session states
# if "file_uploaded" not in st.session_state:
#     st.session_state.file_uploaded = False
# if "input_error" not in st.session_state:
#     st.session_state.input_error = None

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
    
    # # Check input conditions
    # disable_button = False  # Initialize button state
    # feedback_message = None  # Initialize feedback message

    # # Case 1: No input provided
    # if not user_prompt and not uploaded_file:
    #     disable_button = True
    #     feedback_message = "Please provide input by entering text or uploading a .TXT or .PDF file."

    # # Case 2: Both inputs provided
    # elif user_prompt and uploaded_file:
    #     disable_button = True
    #     feedback_message = "Please use only one input method: either enter text or upload a file."
    
    # Debugging to confirm what Streamlit sees
    if uploaded_file:
        st.write("File successfully uploaded:", uploaded_file.name)
    else:
        st.write("No file uploaded yet.")

    # # Submit button
    # submit = st.form_submit_button("Generate Quiz", disabled=disable_button)

    # Submit button
    submit = st.form_submit_button("Generate Quiz")

    # # Display feedback message if necessary
    # if feedback_message:
    #     st.warning(feedback_message)

    # # Status for generating quiz
    # submit = st.form_submit_button("Generate Quiz")

    # # If submit button is clicked and conditions are valid
    # if submit:
    #     # Case: Only file upload
    #     if uploaded_file:
    #         temp_file_path = f"./temp/{uploaded_file.name}"
    #         os.makedirs(os.path.dirname(temp_file_path), exist_ok=True)
    #         with open(temp_file_path, "wb") as f:
    #             f.write(uploaded_file.read())

    #         result = subprocess.run(
    #             [
    #                 sys.executable,
    #                 "generate_quiz_on_file.py",
    #                 "--file_path",
    #                 temp_file_path,
    #                 "--difficulty",
    #                 difficulty_level.lower(),
    #                 "--number_of_questions",
    #                 str(number_of_questions),
    #             ],
    #             capture_output=True,
    #             text=True,
    #         )

    #         if result.returncode == 0:
    #             st.success("Quiz Generated Successfully!")
    #             try:
    #                 quiz_data = json.loads(result.stdout)
    #                 st.json(quiz_data)  # Display quiz JSON
    #             except json.JSONDecodeError:
    #                 st.error("Failed to parse quiz data.")
    #         else:
    #             st.error("Quiz generation failed. Check the logs.")
    #             st.text(result.stderr)

    #     # Case: Only user input
    #     elif user_prompt:
    #         generate_quiz(number_of_questions, difficulty_level, user_prompt)

# Generate quiz if submit button is clicked
if submit:
    # validate_user_input(user_prompt)
    generate_quiz(number_of_questions, difficulty_level, user_prompt)

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