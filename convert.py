#!/usr/bin/env python3
"""
Markdown to HTML Blog Converter

Converts markdown files to styled HTML blog posts using pandoc and custom templates.
Minimal dependencies: Python stdlib + pandoc + pyyaml.
"""

import subprocess
import re
import os
import sys
import tempfile
import glob as glob_module
from datetime import datetime
from pathlib import Path

try:
    import yaml
except ImportError:
    print("Error: pyyaml not installed.")
    print("Install dependencies with: uv sync")
    sys.exit(1)


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 convert.py <markdown_file>    - Convert a single markdown file")
        print("  python3 convert.py travel             - Build the travel lore page")
        sys.exit(1)

    if sys.argv[1] == "travel":
        build_travel_page()
        return

    md_file = sys.argv[1]
    if not os.path.exists(md_file):
        print(f"Error: File {md_file} not found")
        sys.exit(1)

    output_file = generate_output_filename(md_file)
    convert_blog_post(md_file, output_file)
    print(f"Converted {md_file} → {output_file}")


def generate_output_filename(md_file):
    """Generate output HTML filename from input markdown file."""
    path = Path(md_file)
    return str(path.with_suffix('.html'))


def parse_frontmatter(md_file):
    """Extract YAML frontmatter and remaining markdown content."""
    with open(md_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check for YAML frontmatter (--- ... ---)
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

    # No frontmatter - return empty dict and full content
    return {}, content


def write_temp_markdown(md_content):
    """Write markdown content to temporary file for pandoc processing."""
    temp = tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8')
    temp.write(md_content)
    temp.close()
    return temp.name


def post_process_html(html_content):
    """Remove duplicate h1 that pandoc generates from markdown # header."""
    # Remove first <h1> tag (title is already in preamble)
    html_content = re.sub(r'<h1[^>]*>.*?</h1>\s*', '', html_content, count=1, flags=re.DOTALL)
    return html_content


def convert_blog_post(md_file, output_file):
    """Main conversion function: markdown → styled HTML blog post."""
    metadata, md_content = extract_metadata(md_file)

    # Write temporary file without frontmatter for pandoc
    temp_md = write_temp_markdown(md_content)

    try:
        content_html = convert_with_pandoc(temp_md)
        content_html = post_process_html(content_html)
        css_path = get_css_path(md_file)

        final_html = generate_html_template(metadata, content_html, css_path, md_file)

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(final_html)

        print(f"Extracted metadata: {metadata}")
        print(f"Generated {len(content_html)} chars of HTML content")
    finally:
        # Clean up temp file
        if os.path.exists(temp_md):
            os.unlink(temp_md)


def generate_html_template(metadata, content_html, css_path, md_file):
    """Generate complete HTML document with blog template."""
    authors_html = format_authors(metadata['authors'])

    template = f"""<!DOCTYPE html>
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
    return template


def get_css_path(md_file):
    """Calculate relative path to CSS files from the markdown file location."""
    md_path = Path(md_file).resolve()  # Resolve to absolute path

    # Count directory depth from root of blog
    # If file is in notes/2024-05-25/file.md, we need to go up 2 levels: ../../
    # If file is in posts/2023-08-26/file.md, we need to go up 2 levels: ../../

    # Assume the blog root is where we are running the script from
    blog_root = Path.cwd().resolve()
    try:
        relative_path = md_path.parent.relative_to(blog_root)
        depth = len(relative_path.parts)
    except ValueError:
        # File is not relative to current directory, assume depth of 1
        depth = 1

    # Generate relative path string
    if depth == 0:
        return "."  # Same directory
    else:
        return "/".join([".."] * depth)


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

    # Fallback: return generic title
    return "Blog Post"


def extract_date_from_path(md_file):
    """Extract date from directory path (e.g., notes/2024-05-25/ or posts/2023-08-26/)."""
    path_parts = Path(md_file).parts

    # Look for date pattern in path (YYYY-MM-DD)
    date_pattern = r'(\d{4}-\d{2}-\d{2})'
    for part in path_parts:
        match = re.search(date_pattern, part)
        if match:
            date_str = match.group(1)
            # Convert to [YYYY-MM-DD] format
            return f'[{date_str}]'

    # Fallback: current date
    return f'[{datetime.now().strftime("%Y-%m-%d")}]'


# ============================================================================
# Travel Lore Page Builder
# ============================================================================

def build_travel_page():
    """Build the travel lore page with annotated map from markdown entries."""
    travel_dir = Path("travel")

    if not travel_dir.exists():
        print("Error: travel/ directory not found")
        sys.exit(1)

    # Find all markdown files in travel directory
    md_files = sorted(glob_module.glob(str(travel_dir / "*.md")), reverse=True)

    if not md_files:
        print("No markdown files found in travel/ directory")
        print("Create entries like: travel/kyoto-2024.md")
        sys.exit(1)

    entries = []
    pins = []

    for md_file in md_files:
        entry = parse_travel_entry(md_file)
        if entry:
            entries.append(entry)
            if entry.get('coords'):
                pins.append(generate_map_pin(entry))

    # Load base map and inject pins
    map_svg = load_and_populate_map(pins)

    # Generate the HTML page
    html = generate_travel_html(map_svg, entries)

    output_file = travel_dir / "index.html"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"Built travel page with {len(entries)} entries → {output_file}")


def parse_travel_entry(md_file):
    """Parse a travel markdown file and return entry data."""
    frontmatter, md_content = parse_frontmatter(md_file)

    if not frontmatter:
        print(f"Warning: No frontmatter in {md_file}, skipping")
        return None

    # Convert markdown to HTML
    temp_md = write_temp_markdown(md_content)
    try:
        content_html = convert_with_pandoc(temp_md)
        # Remove h1 if present (title is in header)
        content_html = re.sub(r'<h1[^>]*>.*?</h1>\s*', '', content_html, count=1, flags=re.DOTALL)
    finally:
        if os.path.exists(temp_md):
            os.unlink(temp_md)

    # Extract entry ID from filename if not specified
    entry_id = frontmatter.get('id') or Path(md_file).stem

    return {
        'id': entry_id,
        'title': frontmatter.get('title', 'Untitled'),
        'date': frontmatter.get('date', ''),
        'location': frontmatter.get('location', ''),
        'coords': frontmatter.get('coords'),  # [lat, lon]
        'content': content_html
    }


def coords_to_svg(lat, lon, width=1000, height=500):
    """Convert lat/lon coordinates to SVG x/y position."""
    # Simple equirectangular projection
    x = (lon + 180) * (width / 360)
    y = (90 - lat) * (height / 180)
    return x, y


def generate_map_pin(entry):
    """Generate SVG pin element for a travel entry."""
    lat, lon = entry['coords']
    x, y = coords_to_svg(lat, lon)

    return f'''    <a href="#{entry['id']}" class="pin-link">
      <circle cx="{x:.1f}" cy="{y:.1f}" r="6" class="map-pin"/>
      <title>{entry['location']}</title>
    </a>'''


def load_and_populate_map(pins):
    """Load the base map SVG and insert pins."""
    map_path = Path("travel/world-map.svg")

    if not map_path.exists():
        print("Warning: travel/world-map.svg not found, creating empty map")
        return '<svg viewBox="0 0 1000 500" class="travel-map"></svg>'

    with open(map_path, 'r', encoding='utf-8') as f:
        svg_content = f.read()

    # Replace the pins placeholder with actual pins
    pins_content = '\n'.join(pins)
    svg_content = svg_content.replace('<!-- PINS_PLACEHOLDER -->', pins_content)

    # Remove the XML declaration and svg tags - we'll embed just the inner content
    # but keep it as complete SVG for embedding
    return svg_content


def generate_travel_html(map_svg, entries):
    """Generate the complete travel lore HTML page."""

    # Build entries HTML
    entries_html = []
    for entry in entries:
        entry_html = f'''
    <section id="{entry['id']}" class="travel-entry">
      <h2 class="entry-title">{entry['title']}</h2>
      <div class="entry-meta">
        <span class="entry-location">{entry['location']}</span>
        <span class="entry-date">{entry['date']}</span>
      </div>
      {entry['content']}
    </section>'''
        entries_html.append(entry_html)

    entries_combined = '\n'.join(entries_html)

    template = f'''<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <meta name="description" content="travel lore - sid sharma's blog" />

    <title>travel lore</title>

    <link rel="icon" type="image/svg+xml" href="/images/favicon.svg">

    <link rel="stylesheet" href="../styles.css" />
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Lora&family=Space+Mono&display=swap" rel="stylesheet">

    <style>
      /* Travel-specific styles */
      .travel-map {{
        width: 100%;
        max-width: 700px;
        margin: 1.5em auto;
        display: block;
      }}

      .travel-map .continents path {{
        fill: none;
        stroke: rgb(200, 200, 200);
        stroke-width: 1;
      }}

      .travel-map .map-pin {{
        fill: rgb(21, 70, 175);
        cursor: pointer;
        transition: all 0.2s ease;
      }}

      .travel-map .map-pin:hover {{
        fill: rgb(41, 90, 195);
        r: 9;
      }}

      .travel-map .pin-link {{
        text-decoration: none;
      }}

      .travel-entry {{
        margin: 3em 0;
        padding-top: 1.5em;
        border-top: 1px solid rgb(230, 230, 230);
        scroll-margin-top: 2em;
      }}

      .travel-entry:first-of-type {{
        border-top: none;
      }}

      .entry-title {{
        font-style: normal;
        font-size: 1.3em;
        margin-bottom: 0.3em;
      }}

      .entry-meta {{
        color: rgb(109, 109, 109);
        font-style: italic;
        margin-bottom: 1em;
      }}

      .entry-location::after {{
        content: " · ";
      }}

      .map-intro {{
        text-align: center;
        color: rgb(109, 109, 109);
        margin-bottom: 0.5em;
      }}
    </style>
</head>

<body>
    <div id="preamble">
        <a href="/travel/">
            <h1 class="title">travel lore</h1>
        </a>
        <p class="map-intro">click a pin to jump to the entry</p>
        <hr>
    </div>

    <div class="map-container">
      {map_svg}
    </div>

    <div class="entries">
      {entries_combined}
    </div>

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

</html>'''
    return template


if __name__ == "__main__":
    main()