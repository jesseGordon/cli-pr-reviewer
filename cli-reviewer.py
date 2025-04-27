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
        sys.stdout.write("\r")
        sys.stdout.flush()

    def start(self):
        self.busy = True
        threading.Thread(target=self._spin).start()

    def stop(self):
        self.busy = False
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
    result = subprocess.run(cmd, stdout=subprocess.PIPE, text=True)
    return result.stdout


def make_prompt(diff_text):
    """
    Construct the prompt for the Gemini API.
    """
    return (
        """
        You're an expert software engineer performing a detailed code review. Evaluate the provided pull request (PR) carefully, considering correctness, readability, efficiency, adherence to best practices, and potential edge cases or bugs. Provide constructive feedback highlighting specific issues or suggestions for improvements. Conclude your review explicitly with either `APPROVED` if the PR meets high standards and can be merged without further changes, or `MAKE CHANGES` if revisions are required, clearly stating your reasoning.

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


def send_to_gemini(prompt, api_key):
    """
    Send the prompt to the Gemini API and return the response text.
    """
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.5-flash-preview-04-17")
    response = model.generate_content(prompt)
    return response.text


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
    review = send_to_gemini(prompt, api_key)
    spinner.stop()

    print("\nGemini PR Review:\n")
    print(review)


if __name__ == "__main__":
    main()

