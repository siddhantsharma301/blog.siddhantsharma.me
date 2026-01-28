"""Shared utilities for blog conversion."""

import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml


def parse_frontmatter(md_file):
    """Extract YAML frontmatter and remaining markdown content."""
    with open(md_file, 'r', encoding='utf-8') as f:
        content = f.read()

    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            try:
                frontmatter = yaml.safe_load(parts[1])
                markdown_content = parts[2].strip()
                return frontmatter or {}, markdown_content
            except yaml.YAMLError as e:
                print(f"Warning: Failed to parse YAML frontmatter: {e}")
                return {}, content

    return {}, content


def convert_with_pandoc(md_file):
    """Convert markdown to HTML using pandoc."""
    try:
        result = subprocess.run(
            ['pandoc', '-f', 'markdown', '-t', 'html', md_file],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running pandoc: {e}")
        print(f"stderr: {e.stderr}")
        sys.exit(1)
    except FileNotFoundError:
        print("Error: pandoc not found. Please install pandoc.")
        sys.exit(1)


def strip_first_h1(html_content):
    """Remove duplicate h1 that pandoc generates from markdown # header."""
    return re.sub(r'<h1[^>]*>.*?</h1>\s*', '', html_content, count=1, flags=re.DOTALL)


def get_css_path(md_file):
    """Calculate relative path to CSS files from the markdown file location."""
    md_path = Path(md_file).resolve()
    blog_root = Path.cwd().resolve()

    try:
        relative_path = md_path.parent.relative_to(blog_root)
        depth = len(relative_path.parts)
    except ValueError:
        depth = 1

    if depth == 0:
        return "."
    else:
        return "/".join([".."] * depth)


def write_temp_markdown(md_content):
    """Write markdown content to temporary file for pandoc processing."""
    temp = tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8')
    temp.write(md_content)
    temp.close()
    return temp.name


def cleanup_temp_file(temp_path):
    """Remove temporary file if it exists."""
    if os.path.exists(temp_path):
        os.unlink(temp_path)
