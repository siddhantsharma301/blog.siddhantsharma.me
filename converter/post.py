"""Blog post conversion - markdown to styled HTML."""

import re
from datetime import datetime
from pathlib import Path

from .common import (
    cleanup_temp_file,
    convert_with_pandoc,
    get_css_path,
    parse_frontmatter,
    strip_first_h1,
    write_temp_markdown,
)


def convert(md_file, output=None, verbose=False):
    """Convert a markdown file to a styled HTML blog post."""
    md_path = Path(md_file)

    if not md_path.exists():
        raise FileNotFoundError(f"File {md_file} not found")

    output_file = output or str(md_path.with_suffix('.html'))
    metadata, md_content = extract_metadata(md_file)

    temp_md = write_temp_markdown(md_content)
    try:
        content_html = convert_with_pandoc(temp_md)
        content_html = strip_first_h1(content_html)
        css_path = get_css_path(md_file)

        final_html = generate_html(metadata, content_html, css_path, md_file)

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(final_html)

        if verbose:
            print(f"Extracted metadata: {metadata}")
            print(f"Generated {len(content_html)} chars of HTML content")

        print(f"Converted {md_file} -> {output_file}")
    finally:
        cleanup_temp_file(temp_md)


def extract_metadata(md_file):
    """Extract metadata from YAML frontmatter or fallback to defaults."""
    frontmatter, md_content = parse_frontmatter(md_file)

    metadata = {
        'title': frontmatter.get('title') or extract_title_from_content(md_content),
        'authors': frontmatter.get('authors', [{'name': 'Sid Sharma'}]),
        'date': frontmatter.get('date') or extract_date_from_path(md_file)
    }
    return metadata, md_content


def extract_title_from_content(md_content):
    """Fallback: extract title from first # header in markdown content."""
    for line in md_content.split('\n'):
        line = line.strip()
        if line.startswith('# '):
            return line[2:].strip()
    return "Blog Post"


def extract_date_from_path(md_file):
    """Extract date from directory path (e.g., notes/2024-05-25/)."""
    path_parts = Path(md_file).parts
    date_pattern = r'(\d{4}-\d{2}-\d{2})'

    for part in path_parts:
        match = re.search(date_pattern, part)
        if match:
            return f'[{match.group(1)}]'

    return f'[{datetime.now().strftime("%Y-%m-%d")}]'


def format_authors(authors):
    """Convert author list to HTML with optional links."""
    author_parts = []

    for author in authors:
        name = author['name']
        url = author.get('url')

        if url:
            author_html = f'<a href="{url}" style="color:rgb(109, 109, 109)">{name}</a>'
        else:
            author_html = name

        author_parts.append(author_html)

    return ', '.join(author_parts)


def generate_html(metadata, content_html, css_path, md_file):
    """Generate complete HTML document with blog template."""
    authors_html = format_authors(metadata['authors'])

    return f"""<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <meta name="description" content="sid sharma's blog" />

    <title>{metadata['title']}</title>

    <link rel="icon" type="image/svg+xml" href="/images/favicon.svg">

    <link rel="stylesheet" href="{css_path}/styles.css" />
    <link rel="stylesheet" href="{css_path}/prism.css" />
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Lora&family=Space+Mono&display=swap" rel="stylesheet">
</head>

<body>
    <div id="preamble">
        <a href="{Path(md_file).with_suffix('.html').name}">
            <h1 class="title">{metadata['title']}</h1>
        </a>
        <div class="authors">
            {authors_html}
            <span style="float: right;">
                {metadata['date']}
            </span>
        </div>
        <hr>
    </div>

    {content_html}

    <footer>
        <hr>
        <div class="footer">
            <span style="float: left">
                <a href="/index.html">home</a>
            </span>
            sid's ramblings
        </div>
    </footer>

</body>

</html>"""
