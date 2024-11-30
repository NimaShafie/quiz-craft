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
from fpdf import FPDF

# Function to generate quiz, now accepting selected question types
def generate_quiz(number_of_questions, difficulty_level, user_prompt, question_types):
    with st.status("Generating Quiz...", expanded=True) as status:
        st.write("Running through LLM...")
        quiz_data = run_generate_quiz_script(number_of_questions, difficulty_level, user_prompt, question_types)
        
        if quiz_data:
            st.write("Writing the quiz to session state...")
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

# Function to run the generate_quiz_from_prompt.py script with question types included
def run_generate_quiz_script(number_of_questions, difficulty_level, user_prompt, question_types):
    # Print out the parameters for debugging
    print(f"Running generate_quiz_from_prompt.py with arguments: {number_of_questions}, {difficulty_level}, {user_prompt}, {question_types}")
    
    # Prepare the list of selected question types to pass to the script
    question_types_str = ','.join(question_types)

    # Running the subprocess to generate the quiz
    result = subprocess.run([sys.executable, 'generate_quiz_from_prompt.py',
                             str(number_of_questions), difficulty_level, user_prompt, question_types_str],
                             capture_output=True, text=True, timeout=120)

    print(f"\nRaw result.stdout: {repr(result.stdout)}")  # Debug output

    # Clean up result.stdout: Strip unnecessary whitespace and newlines
    cleaned_stdout = result.stdout.strip()

    # Regex to extract the JSON block starting with '{' and ending with '}'f
    match = re.search(r'(\{.*\})', cleaned_stdout, re.DOTALL)  # re.DOTALL allows '.' to match newlines
    if match:
        json_data = match.group(1)
        print(f"\n\nCleaned JSON data: {repr(json_data)}")  # Debugging the extracted JSON data

        # Try parsing the extracted JSON
        try:
            quiz_data = json.loads(json_data)  # Parse the JSON to get the quiz data
            print(f"\n\nParsed quiz data successfully: {quiz_data}")

        except json.JSONDecodeError as e:
            print(f"\nJSONDecodeError: {e}")
            quiz_data = None
    else:
        print("\nNo valid JSON response found in stdout.")
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
        question_type = quiz.get('type', '').strip().lower()  # Normalize type to lowercase and strip spaces

        # Handle different question types
        if question_type == "multiple choice":
            # Format options as 'a.', 'b.', 'c.', 'd.'
            for idx, option in enumerate(options, 1):
                formatted_quiz += f"   {chr(96 + idx)}. {option}\n"

        elif question_type == "true/false":
            # Display True/False options
            formatted_quiz += "   a. True\n"
            formatted_quiz += "   b. False\n"

        elif question_type == "fill in the blanks":
            # For fill-in-the-blanks, no options to display
            formatted_quiz += "   (Blank space for the answer)\n"

        formatted_quiz += "\n"
        question_number += 1

    # Build the answer key
    formatted_quiz += "\nAnswer Key:\n"
    question_number = 1
    for quiz in quiz_data.get("quiz", []):
        options = quiz.get('options', [])
        correct_answer = quiz.get('answer', "")  # Default to an empty string if no answer is provided
        question_type = quiz.get('type', '').strip().lower()  # Normalize type to lowercase and strip spaces

        # Handle the correct answer display for different question types
        if question_type == "multiple choice" and correct_answer in options:
            # For multiple-choice questions, find the correct option letter (e.g., 'a', 'b', 'c', 'd')
            correct_index = options.index(correct_answer)  # Find the index of the correct answer in options
            correct_letter = chr(97 + correct_index)  # Convert to letter ('a', 'b', 'c', etc.)
            formatted_quiz += f"{question_number}. ({correct_letter}) - {correct_answer}\n"

        elif question_type == "true/false":
            # Ensure correct_answer is handled regardless of type (bool or string)
            if isinstance(correct_answer, bool):
                correct_letter = 'a' if correct_answer else 'b'
                correct_answer = "True" if correct_answer else "False"
            elif isinstance(correct_answer, str):
                correct_letter = 'a' if correct_answer.lower() == 'true' else 'b'
            else:
                correct_letter = "?"
                correct_answer = "Unknown"
            formatted_quiz += f"{question_number}. ({correct_letter}) - {correct_answer}\n"

        elif question_type == "fill in the blanks":
            # For fill-in-the-blank questions, ensure the correct answer is a string, not empty value
            correct_answer = correct_answer.strip() if correct_answer.strip() else "Correct answer is provided."
            formatted_quiz += f"{question_number}. - {correct_answer}\n"

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

# Check input conditions
disable_button = False  # Initialize button state
feedback_message = None  # Initialize feedback message

# Start the container div with the border using st.markdown
st.markdown('<div class="container-with-border">', unsafe_allow_html=True)

# File uploader inside the bordered container
uploaded_file = st.file_uploader("Upload your TXT or PDF file here",
                                    type=["txt", "pdf"], help="Upload a TXT or PDF file")

# st.divider()
st.write("<center>OR</center>", unsafe_allow_html=True)

# Text input area inside the bordered container
user_prompt = st.text_area("Text Input", height=200, max_chars=3500, help="Enter your text here")

# Check if file is uploaded to enable the submit button
file_uploaded = uploaded_file is not None

# Create form
with st.form(key="quiz_form"):

    # Enable button only if file is uploaded
    submit_button_disabled = not file_uploaded  # Disable button if no file uploaded

    # User will be able to select the number of questions for each type
    # Based on what available question types were selected above
    # #input fields
    # mcq_count=st.number_input("No. of MCQs: ", min_value=3, max_value=50, placeholder= "10")

    col1, col2, = st.columns(2, gap="large")
    
    with col1:
        # User selects question types
        question_types = st.multiselect(
            "Question Types", 
            ["Multiple Choice", "True/False", "Fill in the Blanks"],
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
    number_of_questions = st.slider("Number of Questions", min_value=5, max_value=40, value=10,
                                    help="Select the number of questions you want in the quiz"
                                    )
    
    # Logic to enable the submit button based on conditions
    disable_button = True  # Initially, the button is disabled
    if user_prompt.strip() or uploaded_file:  # Check if there's text or a file uploaded
        disable_button = False  # Enable the button if either condition is met
    
    # Enable or disable the submit button based on file upload or text input
    submit_button_disabled = not (uploaded_file or user_prompt.strip())  # Check if file uploaded or text entered

    # # Case 1: No input provided
    if not user_prompt and not uploaded_file:
        submit_button_disabled = True
        feedback_message = "Please provide input by entering text or uploading a .TXT or .PDF file."

    # Case 2: Both inputs provided
    elif user_prompt and uploaded_file:
        submit_button_disabled = True
        feedback_message = "Please use only one input method: either enter text or upload a file."

    # "Generate Quiz" button (disabled initially)
    submit = st.form_submit_button("Generate Quiz", disabled=submit_button_disabled)

    # Provide feedback if file uploaded or not
    if uploaded_file:
        st.write(f"File successfully uploaded: {uploaded_file.name}")

    # Display feedback message if necessary
    if feedback_message:
        st.warning(feedback_message)

# Generate quiz if submit button is clicked
if submit:
    # validate_user_input(user_prompt)
    generate_quiz(number_of_questions, difficulty_level, user_prompt, question_types)
    st.success("Quiz generated!")

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
    st.write(formatted_quiz)