"""
Code for generating quiz based on user prompt.

Created by ZJ
Date : 28 Nov, 2024.

Usage:

generate_quiz_from_prompt.main(difficulty, number_of_questions, user_prompt)

difficulty : <str> easy, medium, hard, extremely hard, etc.
number_of_questions : <str> Ex: "5". This is the number of questions in the quiz.
user_prompt : <str> The quiz will be generated on this prompt.

Sample prompt : Rivers that start with the letter 'N'.

"""
import json
import sys
import streamlit as st
from llama_index.llms.ollama import Ollama
from config_reader import fetch_config_dict

# Function to generate quiz based on user prompt
def generate_quiz(number_of_questions="5", difficulty="easy", user_prompt="", question_types=["Multiple Choice"]):

    config_dict = fetch_config_dict()
    # Initialize the LLM    
    llm = Ollama(config_dict.get("model_name", "advanced_model"),
                 temperature=0.6, json_mode=True)

    # Define the prompt based on the selected question types
    question_type_instructions = {
        "Multiple Choice": "Create a multiple-choice question with four options, where one option is correct.",
        "True/False": "Create a true/false question with the correct answer (True or False).",
        "Fill in the Blanks": "Create a fill-in-the-blanks question with a missing word or phrase."
    }
    
    # Build the prompt dynamically based on selected question types
    question_type_prompt = "\n".join([question_type_instructions[qt] for qt in question_types])

    prompt = f"""
    You are tasked with creating a quiz on the topic: "{user_prompt}". 
    Please generate {number_of_questions} questions at the difficulty level "{difficulty}".
    The questions should be of the following types: {", ".join(question_types)}.
    If there is more than one question type present, keep all the same question types together, create a question of each type before moving to the next type.

    The output should be a JSON object with this structure:
    {{
        "quiz": [
            {{
                "question": "Question text",
                "type": "Question type",
                "options": ["Option1", "Option2", "Option3", "Option4"],
                "answer": "Correct answer"
            }},
            ...
        ]
    }}
    """

    # Blocking call
    resp = llm.complete(prompt)

    # Assuming `resp` is an object with a `.text` attribute or a similar field that contains the raw response:
    response_text = resp.text if hasattr(resp, 'text') else str(resp)
    # print("Model Response Text:", response_text)

    # Ensure the response is a valid JSON string
    try:
        response_json = json.loads(response_text)
        print(json.dumps(response_json, indent=4))

        # Extract the quiz data
        quiz_data = response_json.get("quiz", [])
        
        # # Check if the quiz data is empty
        # if not quiz_data:
        #     # print("Quiz data is empty or not found.")
        # else:
        #     # print("Quiz data retrieved successfully.")
            
        return {"quiz": quiz_data}
    
    except json.JSONDecodeError as e:
        print(f"JSONDecodeError: {e}")
        return {"quiz": []}

# Main function
def main():
    if len(sys.argv) != 5:
        print("Usage: python generate_quiz_from_prompt.py <number_of_questions> <difficulty> <user_prompt> <question_types>")
        return

    number_of_questions = int(sys.argv[1])
    difficulty = sys.argv[2]
    user_prompt = sys.argv[3]
    question_types = sys.argv[4].split(",")  # Expecting a comma-separated string of question types

    # Call the blocking version of generate_quiz (no async)
    response = generate_quiz(number_of_questions, difficulty, user_prompt, question_types)

    # # If response is successful
    # if response and response.get("quiz"):
    #     print("Quiz generated successfully!")
    #     print(f"Quiz Data: {json.dumps(response, indent=4)}")
    # else:
    #     print("Failed to generate quiz.")

if __name__ == "__main__":
    main()
    