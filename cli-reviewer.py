#!/usr/bin/env python3

import subprocess
import argparse
import os
import sys
import time
import threading
import textwrap
import google.generativeai as genai
import shutil


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
        threading.Thread(target=self._spin, daemon=True).start()

    def stop(self):
        self.busy = False
        time.sleep(self.delay)


def get_git_diff(diff_args):
    """
    Return the output of `git diff` with the given arguments.
    If no arguments are provided, defaults to staged changes.
    """
    cmd = ["git", "diff"] + diff_args if diff_args else ["git", "diff", "--cached"]
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error executing git diff: {e.stderr}", file=sys.stderr)
        sys.exit(1)


def make_prompt(diff_text):
    """
    Construct the prompt for the Gemini API in Markdown.
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


def send_to_gemini(prompt, api_key):
    """
    Send the prompt to the Gemini API and return the response stream iterator.
    """
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.5-flash-preview-04-17")
    return model.generate_content(prompt, stream=True)


def main():
    parser = argparse.ArgumentParser(description="Review Git diffs using Gemini API.")
    parser.add_argument("diff_args", nargs=argparse.REMAINDER, help="Arguments to pass to git diff")
    args = parser.parse_args()

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable not set.", file=sys.stderr)
        print("Set it with: export GEMINI_API_KEY=your_api_key", file=sys.stderr)
        sys.exit(1)

    diff_text = get_git_diff(args.diff_args)
    if not diff_text.strip():
        print("No changes found.", file=sys.stderr)
        sys.exit(0)

    prompt = make_prompt(diff_text)
    print("Sending diff to Gemini for review...", file=sys.stderr)

    spinner = Spinner("Waiting for Gemini")
    spinner.start()
    review_stream = send_to_gemini(prompt, api_key)
    spinner.stop()

    print("\nGemini PR Review:\n", file=sys.stderr)

    # Decide whether to use bat or fallback
    bat_path = shutil.which("bat")
    use_bat = bat_path is not None and sys.stdout.isatty()

    if use_bat:
        # Stream into bat for markdown highlighting
        proc = subprocess.Popen(
            [bat_path, "--language=markdown", "--paging=never"],
            stdin=subprocess.PIPE,
            text=True
        )
        for chunk in review_stream:
            if hasattr(chunk, "text"):
                proc.stdin.write(chunk.text)
                proc.stdin.flush()
        proc.stdin.close()
        proc.wait()
    else:
        # Fallback: plain stdout streaming
        if bat_path is None:
            print("[Note] 'bat' not found; falling back to plain output.\n", file=sys.stderr)
        for chunk in review_stream:
            if hasattr(chunk, "text"):
                print(chunk.text, end="", flush=True)
        print()  # final newline


if __name__ == "__main__":
    main()