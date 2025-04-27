#!/usr/bin/env python3

import subprocess
import argparse
import os
import sys
import time
import threading
import google.generativeai as genai

class Spinner:
    """
    Simple spinner for indicating progress in the terminal.
    """
    def __init__(self, message="Waiting"):
        self.message = message
        self.busy = False
        self.spinner = self._spinner_generator()
        self.delay = 0.1

    def _spinner_generator(self):
        while True:
            for cursor in '|/-\\':
                yield cursor

    def _spin(self):
        while self.busy:
            sys.stdout.write(f"\r{self.message} {next(self.spinner)}")
            sys.stdout.flush()
            time.sleep(self.delay)
        # Original clearing behavior: write \r, flush
        sys.stdout.write("\r")
        sys.stdout.flush()

    def start(self):
        self.busy = True
        threading.Thread(target=self._spin).start()

    def stop(self):
        self.busy = False
        # Original delay after setting busy to False
        time.sleep(self.delay)


def get_git_diff(diff_args):
    """
    Return the output of `git diff` with the given arguments.
    If no arguments are provided, defaults to staged changes.
    """
    if diff_args:
        cmd = ["git", "diff"] + diff_args
    else:
        cmd = ["git", "diff", "--cached"]
    # Original subprocess call without extra error handling
    result = subprocess.run(cmd, stdout=subprocess.PIPE, text=True)
    return result.stdout


def make_prompt(diff_text):
    """
    Construct the prompt for the Gemini API.
    """
    # Original prompt string
    return (
        """
        You're an expert software engineer performing a detailed code review.
        Evaluate the provided pull request (PR) carefully, considering correctness, readability, efficiency, adherence to best practices, and potential edge cases or bugs. Provide constructive feedback highlighting specific issues or suggestions for improvements. Conclude your review explicitly with either `APPROVED` if the PR meets high standards and can be merged without further changes, or `MAKE CHANGES` if revisions are required, clearly stating your reasoning.

        Example response format:


        Feedback:
        - [Specific issue or suggestion #1]
        - [Specific issue or suggestion #2]
        - [Further detailed feedback as needed]

        Conclusion: APPROVED

        or

        Feedback:
        - [Specific issue or suggestion #1]
        - [Specific issue or suggestion #2]
        - [Further detailed feedback as needed]

        Conclusion: MAKE CHANGES"""
        + diff_text
    )


# *** MODIFIED FOR STREAMING ***
def send_to_gemini(prompt, api_key):
    """
    Send the prompt to the Gemini API and return the response stream iterator.
    """
    genai.configure(api_key=api_key)
    # Keep the original model name
    model = genai.GenerativeModel("gemini-2.5-flash-preview-04-17")
    # Call generate_content with stream=True
    response_stream = model.generate_content(prompt, stream=True)
    # Return the iterator itself, not response.text
    return response_stream


def main():
    parser = argparse.ArgumentParser(
        description="Review Git diffs using Gemini API."
    )
    parser.add_argument(
        "diff_args",
        nargs=argparse.REMAINDER,
        help="Arguments to pass to git diff"
    )
    args = parser.parse_args()

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable not set.")
        print("Set it with: export GEMINI_API_KEY=your_api_key")
        sys.exit(1)

    diff_text = get_git_diff(args.diff_args)
    if not diff_text.strip():
        print("No changes found.")
        sys.exit(0)

    prompt = make_prompt(diff_text)
    print("Sending diff to Gemini for review...")

    spinner = Spinner("Waiting for Gemini")
    spinner.start()

    # *** MODIFIED FOR STREAMING ***
    # 'review_stream' now holds the iterator returned by the modified send_to_gemini
    review_stream = send_to_gemini(prompt, api_key)

    # Stop the spinner *after* the call returns the iterator, but *before* consuming it
    spinner.stop()

    print("\nGemini PR Review:\n")
    # Iterate through the stream and print each chunk's text
    try:
        for chunk in review_stream:
            # Print the text part of each chunk as it arrives
            # Use end='' to avoid adding extra newlines between chunks
            # Use flush=True to ensure the output is displayed immediately
            print(chunk.text, end="", flush=True)
        print() # Print a final newline after the stream is complete
    except AttributeError as e:
        # Handle cases where a chunk might not have 'text', minimally
        # (This could happen with safety feedback or other metadata)
        print(f"\n[Encountered non-text chunk: {e}]", file=sys.stderr)
    except Exception as e:
        # General catch for other errors during streaming
        print(f"\n[An error occurred during streaming: {e}]", file=sys.stderr)


if __name__ == "__main__":
    main()