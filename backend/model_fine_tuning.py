"""
model_fine_tuning.py

Stub for fine-tuning the language model on course-specific data.
"""
import openai
import os
from dotenv import load_dotenv

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")


def fine_tune_model(training_file_path: str):
    """
    Stub: Provide a path to a JSONL file with training data.
    For example:
        [
          {"prompt": "<YOUR_PROMPT>", "completion": "<DESIRED_OUTPUT>"}
        ]
    In reality, you'd call:
        openai.FineTune.create(training_file=training_file_path, ...)
    """
    print("Fine-tuning model with:", training_file_path)
    # This is where you'd invoke openai.FineTune.create(...)
    # e.g.:
    # response = openai.FineTune.create(
    #     training_file=training_file_path,
    #     model="gpt-3.5-turbo",
    #     ...
    # )
    # print(response)
    pass


if __name__ == "__main__":
    fine_tune_model("./path/to/training_data.jsonl")
