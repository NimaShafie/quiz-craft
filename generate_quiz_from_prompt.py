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

from llama_index.llms.ollama import Ollama
import asyncio
from config_reader import fetch_config_dict

# Generate quiz using Async for faster response
async def generate_quiz(number_of_questions = "5", difficulty = "easy", user_prompt = ""):

    config_dict = fetch_config_dict()
    # Initialize the LLM
    llm = Ollama(model=config_dict.get("model_name", "basic_model"), 
                 request_timeout=120.0, 
                 json_mode=True)

    # Define the improved prompt
    prompt = """Give me an MCQ quiz on {}.
                I want {} questions.
                The difficulty of the quiz should be {}.""".format(user_prompt, number_of_questions, difficulty)
    
    prompt_2 = """
                
                Give the answers as well. Output as a structured JSON object.
                Output in the following JSON format:
        {
            "quiz": [
                {
                    "question": "Question text here",
                    "options": ["Option1", "Option2", "Option3", "Option4"],
                    "answer": "Correct Option"
                },
                ...
            ]
        }
                        
                        """
    
    prompt += prompt_2
    print(prompt)
    try:
        # Use `await` for the async call
        resp = await llm.acomplete(prompt)
        #print("Response:\n", str(resp))
    except Exception as e:
        print(f"An error occurred: {e}")
        resp = "Error occured while generating the quiz on user prompt only." + str(e)

    return resp

# Main
def main(number_of_questions, difficulty, user_prompt):

    response = asyncio.run(generate_quiz(number_of_questions, difficulty, user_prompt))
    return response



if __name__ == "__main__":

    user_prompt = "The history of California"
    number_of_questions = 10 
    difficulty = "hard"
    
    print(main(number_of_questions, difficulty, user_prompt))