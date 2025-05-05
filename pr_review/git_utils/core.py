"""Git utilities for PR Review CLI."""

import subprocess
from typing import List, Optional, Dict, Any
from ..exceptions import PrReviewError

def construct_diff_command(staged: bool = False, unstaged: bool = False, 
                         file_path: Optional[str] = None, commit: Optional[str] = None, 
                         diff_args: List[str] = None) -> List[str]:
    """
    Construct git diff command based on options.
    
    Args:
        staged: Get staged changes
        unstaged: Get unstaged changes 
        file_path: Get diff for specific file
        commit: Get diff for specific commit or commit range
        diff_args: Additional args to pass to git diff
        
    Returns:
        List[str]: The command to run as a list of strings
    """
    cmd = ["git", "diff"]
    
    if staged:
        cmd.append("--cached")
    elif file_path:
        cmd.append("--")
        cmd.append(file_path)
    elif commit:
        # Support specific commit or commit range
        if ".." in commit:
            # It's a range
            cmd.append(commit)
        else:
            # Single commit
            cmd.append(f"{commit}^..{commit}")
    elif diff_args:
        cmd.extend(diff_args)
    elif not unstaged:  # Default to staged if nothing specified
        cmd.append("--cached")
    
    return cmd


def get_git_diff(staged: bool = False, unstaged: bool = False, 
                file_path: Optional[str] = None, commit: Optional[str] = None, 
                diff_args: List[str] = None, max_chars: Optional[int] = None) -> str:
    """
    Return the output of `git diff` with the given arguments.
    
    Args:
        staged: Get staged changes
        unstaged: Get unstaged changes
        file_path: Get diff for specific file
        commit: Get diff for specific commit
        diff_args: Additional args to pass to git diff
        max_chars: Maximum number of characters to include in the diff
        
    Returns:
        str: The git diff text
        
    Raises:
        PrReviewError: If there is an error running git diff
    """
    cmd = construct_diff_command(staged, unstaged, file_path, commit, diff_args)
    
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        diff_text = result.stdout
        
        if max_chars and len(diff_text) > max_chars:
            # Truncate the diff text - a more intelligent approach might truncate by full hunks
            # but that would require parsing the diff format which is complex
            truncated_message = f"\n\n[Diff truncated to {max_chars} characters. Original size: {len(diff_text)} characters]"
            diff_text = diff_text[:max_chars] + truncated_message
        
        return diff_text
    except subprocess.CalledProcessError as e:
        raise PrReviewError(f"Git error: {e.stderr.strip()}", exit_code=3) 