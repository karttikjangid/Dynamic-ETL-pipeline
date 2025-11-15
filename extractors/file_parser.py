"""Helpers for reading and parsing supported file types."""

from __future__ import annotations

from pathlib import Path
from typing import List


def parse_file(file_path: str) -> str:
    """Dispatch parsing based on extension."""

    path = Path(file_path)
    suffix = path.suffix.lower()
    if suffix == ".md":
        return parse_md_file(file_path)
    if suffix == ".txt":
        return parse_txt_file(file_path)
    raise ValueError(f"Unsupported file type: {suffix}")


def parse_txt_file(file_path: str) -> str:
    """Return plain text content.
    
    Args:
        file_path: Path to the .txt file
        
    Returns:
        Raw text content as string
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()


def parse_md_file(file_path: str) -> str:
    """Return markdown content as-is.
    
    Args:
        file_path: Path to the .md file
        
    Returns:
        Raw markdown content as string
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()


def extract_code_blocks(md_content: str) -> List[str]:
    """Extract fenced code blocks from Markdown content.
    
    Finds code blocks delimited by triple backticks (```).
    
    Args:
        md_content: Markdown text content
        
    Returns:
        List of code block contents (without the backticks)
    """
    code_blocks = []
    lines = md_content.split('\n')
    in_code_block = False
    current_block = []
    
    for line in lines:
        # Check for code block delimiter
        if line.strip().startswith('```'):
            if in_code_block:
                # End of code block
                code_blocks.append('\n'.join(current_block))
                current_block = []
                in_code_block = False
            else:
                # Start of code block
                in_code_block = True
        elif in_code_block:
            current_block.append(line)
    
    # Handle unclosed code block
    if current_block:
        code_blocks.append('\n'.join(current_block))
    
    return code_blocks
