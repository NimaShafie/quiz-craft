"""
Code for generating embeddings (Using Ollama) and querying on the generated index.
Created by ZJ
Date : 28 Nov, 2024.

Usage:

generate_quiz_from_files.main(difficulty, number_of_questions, user_prompt)

difficulty : <str> easy, medium, hard, extremely hard, etc.
number_of_questions : <str> Ex: "5". This is the number of questions in the quiz.
user_prompt : <str> If empty, the quiz will be generated on the entire document as it is.

"""

from llama_index.llms.ollama import Ollama
from llama_index.core import Settings, SimpleDirectoryReader, VectorStoreIndex
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.readers.file import PDFReader
from llama_index.extractors.entity import EntityExtractor
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.ingestion import IngestionPipeline
from config_reader import fetch_config_dict

# PERSIST_DIR = './INDEX'

# Setup LLM
def llm_setup(config_dict):
    """
    This function sets up the configuration for:
        1. Trasformation
        2. Embedding Model
        3. LLM

    Returns : None
    """

    # Configuring Transformations
    entity_extractor = EntityExtractor(
        prediction_threshold=0.5,
        label_entities=False,  # include the entity label in the metadata (can be erroneous)
        device=config_dict.get("device", "cpu"),  # set to "cuda" if you have a GPU
    )

    node_parser = SentenceSplitter()

    transformations = [node_parser, entity_extractor]

    # Configuring Embedding Model
    ollama_embedding = OllamaEmbedding(
        model_name=config_dict.get("model_name", "basic_model"),
        base_url="http://localhost:11434",
        ollama_additional_kwargs={"mirostat": 0},
    )

    # Configure LLM
    llm = Ollama(config_dict.get("model_name", "basic_model"), temperature=0.2, json_mode=True)

    # Store all values in Settings
    Settings.llm = llm
    Settings.embed_model = ollama_embedding
    Settings.transformations = transformations

    return


# Load PDF Files
def load_pdf_files(config_dict):

    # PDF Reader with `SimpleDirectoryReader`
    parser = PDFReader()
    file_extractor = {".pdf": parser}
    documents = SimpleDirectoryReader(
        config_dict.get("data_directory", "./data"), file_extractor=file_extractor
    ).load_data()

    return documents

# Create Nodes from the document
def create_nodes(documents):
    """
    This function creates nodes on the document. This can then be turned into embeddings.
    """
    pipeline = IngestionPipeline(transformations=Settings.transformations)
    nodes = pipeline.run(documents=documents)

    return nodes

# Create Index on Nodes
def create_index(nodes):
    """
    This function creates the indices on the input document nodes
    Input : nodes <list>
    returns : Indices
    
    """
    index = VectorStoreIndex(nodes=nodes)
    
    # Save Index to storage
    # index.storage_context.persist(persist_dir=PERSIST_DIR)
    # print("Index saved")

    return index

# Query on the index
def query_on_index(index, difficulty, number_of_questions, user_prompt = ""):
    """
    This function queries on the index with the default prompt.

    """

    prompt = """Give me an MCQ quiz on this document.
                I want {} questions.
                The difficulty of the quiz should be {}.""".format(number_of_questions, difficulty)
    
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
    if user_prompt.strip() != "":
        prompt += '\n' + user_prompt
    prompt += prompt_2

    print("Prompt : ", prompt)

    query_engine = index.as_query_engine()
    response = query_engine.query(prompt)
    return response

# Main
def main(difficulty = 'easy', number_of_questions = '5', user_prompt = ""):

    config_dict = fetch_config_dict()

    print("CONFIG DICT : ", config_dict)

    llm_setup(config_dict)
    documents = load_pdf_files(config_dict)
    nodes = create_nodes(documents)
    index = create_index(nodes)
    response = query_on_index(index,difficulty, number_of_questions, user_prompt)
    return response


if __name__ == "__main__":

    difficulty = 'hard'
    number_of_questions = '10'
    user_prompt = "I only want questions about the culture and language."

    print(main(difficulty, number_of_questions, user_prompt))




