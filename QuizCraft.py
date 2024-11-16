import json
import pandas as pd
import streamlit as st
from time import sleep
from stqdm import stqdm

# from dotenv import load_dotenv
# from src.mcq_generator.utils import read_file, get_table_data
# from src.mcq_generator.logger import logging

# set page/theme info
st.set_page_config(
    page_title="QuizCraft - AI Generated Quizzes 🧠📚❓",
    page_icon="📝",
    layout="centered",
    initial_sidebar_state="auto",
    menu_items=None)

# resize logo
st.html("""
  <style>
    [alt=Logo] {
      height: 10rem;
    }
  </style>
        """)

st.logo(
    image="images/logo/quiz-craft-logo.png",
    size="large"
    )

# importing necessary packages from LangChain
from langchain_community.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.chains import SequentialChain

# loading json file
with open("response.json", "r") as file:
    RESPONSE_JSON = json.load(file)

#app title
st.title("QuizCraft 🧠📚❓")

#description
description = st.text("QuizCraft is an AI-powered tool that generates different questions from text.\n"
                     "Simply input some text or upload a PDF/text file, and adjust some parameters.\n"
                     "QuizCraft will generate a quiz for you in seconds! 🚀")

#create form
with st.form("user_inputs"):
    #text input
    text_area = st.text_area("Text Input", height=200, max_chars=4000, help="Enter your text here")

    #file upload
    uploaded_file = st.file_uploader("Upload your PDF or txt file here")

    #subject
    subject = st.text_input("Subject name:", max_chars=20, placeholder="Machine Learning")

    #question type
    question_types = st.multiselect("Question Types", ["Multiple Choice", "True/False", "Fill in the Blanks"],
                                    default=["Multiple Choice"], help="Select the type of questions you want in the quiz")

    # user will be able to select the number of questions for each type
    # based on what available question types were selected above
    # #input fields
    # mcq_count=st.number_input("No. of MCQs: ", min_value=3, max_value=50, placeholder= "10")

    #quiz difficulty
    difficulty_level = st.select_slider("Quiz Difficulty", options=["Easy", "Medium", "Hard"],
                                        value="Medium", help="Select the difficulty level of the quiz")

    #number of questions
    number_of_questions = st.slider("Number of Questions", min_value=5, max_value=50, value=10,
                                    help="Select the number of questions you want in the quiz")

    #Create button
    submit = st.form_submit_button("Generate Quiz")
    text_widget = st.empty()
    progress_widget = st.empty()
    if submit:
        for i in range(101):
            sleep(0.01)
            text_widget.write(i)
            progress_widget.progress(i / 100)

# implement the logic for generating the quiz (this is a placeholder)
# #Check if the button has been clicked and all fields have input
# if button and uploaded_file is not None and subject and tone:
#     with st.spinner("Generating MCQs..."):
#         try:
#             text = read_file(uploaded_file)
#             #count tokens and the cost of API call
#             with get_openai_callback() as cb:
#                 response = generate_evaluate_chain(
#                     {
#                         "text": text,
#                         "number": mcq_count,
#                         "subject": subject,
#                         "tone": tone,
#                         "response_json": json.dumps(RESPONSE_JSON)
#                     }
#                 )

#         except Exception as e:
#             traceback.print_exception(type(e), e, e.__traceback__)
#             st.error("An error was encountered!!") 

#         else:
#             print(f"Total Tokens: {cb.total_tokens}")
#             print(f"Prompt Tokens: {cb.prompt_tokens}")
#             print(f"Completion Tokens: {cb.completion_tokens}")
#             print(f"Total Cost: Only {cb.total_cost}")
#             if isinstance(response, dict):
#                 #Extract the quiz data from the response
#                 quiz=response.get("Quiz", None)
#                 if quiz is not None:
#                     table_data = get_table_data(quiz)
#                     if table_data is not None:
#                         df = pd.DataFrame(table_data)
#                         df.index = df.index + 1
#                         st.table(df)

#                         #Display the review in a text box
#                         st.text_area(label="Review", value= response["review"])
#                     else:
#                         st.error("Error in the table data")

#             else:
#                 st.write(response)