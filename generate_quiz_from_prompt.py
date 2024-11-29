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

import re
import json
import sys
import streamlit as st
from llama_index.llms.ollama import Ollama
import asyncio
from config_reader import fetch_config_dict

# Generate quiz using Async for faster response
def generate_quiz(number_of_questions = "5", difficulty = "easy", user_prompt = ""):

    config_dict = fetch_config_dict()
    # Initialize the LLM
    llm = Ollama(model=config_dict.get("model_name", "basic_model"), 
                 request_timeout=120.0, 
                 json_mode=True)

    # Define the improved prompt
    prompt = f"""
    You are tasked with creating an MCQ quiz on the topic: "{user_prompt}".
    Please generate {number_of_questions} questions with the difficulty level set to "{difficulty}".

    Ensure the output is a valid JSON object with the following structure:
    {{
        "quiz": [
            {{
                "question": "Question text here",
                "options": ["Option1", "Option2", "Option3", "Option4"],
                "answer": "Correct Option"
            }},
            ...
        ]
    }}

    Provide only the JSON object as the response. Do not include any additional text or commentary.
    """

    # Use the blocking call for the LLM (replace `acomplete` with `complete`)
    resp = llm.complete(prompt)  # Blocking call

    # # Print the raw response for debugging
    # print("Raw Response:\n", resp)

    # Assuming `resp` is an object with a `.text` attribute or a similar field that contains the raw response:
    response_text = resp.text if hasattr(resp, 'text') else str(resp)

    # # Print the response text for further inspection
    # print("Raw Response Text:", response_text)

    # Ensure the response is a valid JSON string

    try:
        response_json = json.loads(response_text)
        print(json.dumps(response_json, indent=4))
        
        # print("Parsed JSON Response:\n", json.dumps(response_json, indent=4))

        # Extract the quiz data
        quiz_data = response_json.get("quiz", [])
        
        # Check if the quiz data is empty
        if not quiz_data:
            print("Quiz data is empty or not found.")
        else:
            print("Quiz data retrieved successfully.")
            
        return {"quiz": quiz_data}
    
    except json.JSONDecodeError as e:
        print(f"JSONDecodeError: {e}")
        return {"quiz": []}

# Main function
def main():
    if len(sys.argv) != 4:
        print("Usage: python generate_quiz_from_prompt.py <number_of_questions> <difficulty> <user_prompt>")
        return

    number_of_questions = int(sys.argv[1])
    difficulty = sys.argv[2]
    user_prompt = sys.argv[3]

    # Call the blocking version of generate_quiz (no async)
    response = generate_quiz(number_of_questions, difficulty, user_prompt)

    # if response:
    #     print("(generate_quiz_from_prompt.py): Quiz generated successfully\n")
    #     print(f"Printing the json.dumps(response): {json.dumps(response)}")
    # else:
    #     print("Failed to generate quiz")

if __name__ == "__main__":
    main()