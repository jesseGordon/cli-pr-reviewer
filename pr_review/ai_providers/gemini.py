"""Gemini API provider for PR Review CLI."""

import textwrap
from typing import Any
import google.generativeai as genai

def make_prompt(diff_text: str) -> str:
    """
    Construct the prompt for the AI API in Markdown.
    
    Args:
        diff_text: The git diff text to include in the prompt
        
    Returns:
        str: The formatted prompt for the AI
    """
    header = textwrap.dedent("""
    You're an expert software engineer performing a detailed code review.
    Evaluate the provided pull request (PR) carefully, considering correctness,
    readability, efficiency, adherence to best practices, and potential edge cases
    or bugs. Provide constructive feedback highlighting specific issues or suggestions
    for improvements. Conclude your review explicitly with either `APPROVED` if the PR
    meets high standards and can be merged without further changes, or `MAKE CHANGES`
    if revisions are required, clearly stating your reasoning.

    **Format in MARKDOWN syntax.** Do not wrap your entire response in markdown code fences (like ```markdown ... ```); just provide the raw markdown content starting directly with your feedback or conclusion.
                                 
    Example:

    ```
    ## Title: [Give a title for the PR]
    Feedback:
    - [Specific issue or suggestion #1]
    - [Specific issue or suggestion #2]
    - [Further detailed feedback as needed]
                             
    Commit message:
    - [Commit message]

    Conclusion: APPROVED

    or

    ```
    ## Title: [Give a title for the PR]
    Feedback:
    - [Specific issue or suggestion #1]
    - [Specific issue or suggestion #2]
    - [Further detailed feedback as needed]
                             
    Conclusion: MAKE CHANGES
    """)
    return header + diff_text


def send_to_gemini(prompt: str, api_key: str, model: str) -> Any:
    """
    Send the prompt to the Gemini API and return the response stream iterator.
    
    Args:
        prompt: The prompt to send to the API
        api_key: The API key for Gemini
        model: The model to use
        
    Returns:
        Any: The response stream from the API
    """
    genai.configure(api_key=api_key)
    model_obj = genai.GenerativeModel(model)
    return model_obj.generate_content(prompt, stream=True) 