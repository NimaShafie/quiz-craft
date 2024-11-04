import json
import pandas as pd
import streamlit as st
# from dotenv import load_dotenv
# from src.mcq_generator.utils import read_file, get_table_data
# from src.mcq_generator.logger import logging

# set page info
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

# image test
# st.image(image="images/logo/quiz-craft-logo.png")

# importing necessary packages from LangChain
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.chains import SequentialChain

# loading json file
with open("response.json", "r") as file:
    RESPONSE_JSON = json.load(file)

# # theme settings
# st.set_page_config(
#     page_title="QuizCraft 🧠📚❓",
#     page_icon="📝",
#     layout="wide",
#     initial_sidebar_state="expanded",
# )

#app title
st.title("QuizCraft 🧠📚❓")

#create form
with st.form("user_inputs"):
    #file upload
    uploaded_file = st.file_uploader("Upload your PDF ot txt file here")

    #input fields
    mcq_count=st.number_input("No. of MCQs: ", min_value=3, max_value=50, placeholder= "10")

    #subject
    subject = st.text_input("Subject name:", max_chars=20, placeholder="Machine Learning")

    #Quiz Tone
    tone=st.text_input("Complexity level of Questions", max_chars = 20, placeholder = "Simple")

    #Create button
    button = st.form_submit_button("Generate MCQs")

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