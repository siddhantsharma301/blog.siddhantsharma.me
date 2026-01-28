"""Travel page builder - generate travel lore page with map."""

import glob as glob_module
import sys
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature

from .common import (
    cleanup_temp_file,
    convert_with_pandoc,
    parse_frontmatter,
    strip_first_h1,
    write_temp_markdown,
)


def build(verbose=False):
    """Build the travel lore page with annotated map from markdown entries."""
    travel_dir = Path("travel")

    if not travel_dir.exists():
        print("Error: travel/ directory not found")
        sys.exit(1)

    md_files = sorted(glob_module.glob(str(travel_dir / "*.md")), reverse=True)

    if not md_files:
        print("No markdown files found in travel/ directory")
        print("Create entries like: travel/kyoto-2024.md")
        sys.exit(1)

    entries = []
    for md_file in md_files:
        if verbose:
            print(f"Processing {md_file}")
        entry = parse_entry(md_file)
        if entry:
            entries.append(entry)

    generate_map(entries, travel_dir / "world-map.svg")
    html = generate_html(entries)

    output_file = travel_dir / "index.html"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"Built travel page with {len(entries)} entries -> {output_file}")


def parse_entry(md_file):
    """Parse a travel markdown file and return entry data."""
    frontmatter, md_content = parse_frontmatter(md_file)

    if not frontmatter:
        print(f"Warning: No frontmatter in {md_file}, skipping")
        return None

    temp_md = write_temp_markdown(md_content)
    try:
        content_html = convert_with_pandoc(temp_md)
        content_html = strip_first_h1(content_html)
    finally:
        cleanup_temp_file(temp_md)

    entry_id = frontmatter.get('id') or Path(md_file).stem

    return {
        'id': entry_id,
        'title': frontmatter.get('title', 'Untitled'),
        'date': frontmatter.get('date', ''),
        'location': frontmatter.get('location', ''),
        'coords': frontmatter.get('coords'),
        'content': content_html
    }


def generate_map(entries, output_path, width=10, height=5):
    """Generate SVG map with country borders and clickable pins."""
    fig, ax = plt.subplots(
        figsize=(width, height),
        subplot_kw={'projection': ccrs.Robinson()}
    )

    ax.add_feature(cfeature.OCEAN, facecolor='#e8f4f8', edgecolor='none')
    ax.add_feature(cfeature.LAND, facecolor='#f5f5f5', edgecolor='#cccccc', linewidth=0.3)
    ax.add_feature(cfeature.BORDERS, edgecolor='#cccccc', linewidth=0.2)
    ax.add_feature(cfeature.COASTLINE, edgecolor='#999999', linewidth=0.4)

    ax.set_global()
    ax.spines['geo'].set_visible(True)
    ax.spines['geo'].set_edgecolor('#cccccc')
    ax.spines['geo'].set_linewidth(1)
    ax.set_facecolor('none')

    for entry in entries:
        if entry.get('coords'):
            lat, lon = entry['coords']
            ax.plot(
                lon, lat,
                'o',
                transform=ccrs.PlateCarree(),
                color='#1546af',
                markersize=8,
                url=f"#{entry['id']}"
            )

    plt.tight_layout(pad=0)
    fig.savefig(output_path, format='svg', transparent=True)
    plt.close(fig)


def generate_html(entries):
    """Generate the complete travel lore HTML page."""
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

    return f'''<!DOCTYPE html>
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
      .map-container {{
        width: 100%;
        max-width: 700px;
        margin: 1.5em auto;
      }}

      .map-container img {{
        width: 100%;
        display: block;
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
      <img src="world-map.svg" alt="World Map">
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
