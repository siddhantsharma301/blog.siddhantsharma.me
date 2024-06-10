import argparse
import os
import subprocess
from datetime import datetime
from html.parser import HTMLParser

def valid_date(s):
    try:
        date = datetime.strptime(s, "%Y-%m-%d")
        return date.strftime("%Y-%m-%d")
    except ValueError:
        raise argparse.ArgumentTypeError(f"Not a valid date: '{s}'. Expected format: YYYY-MM-DD")

parser = argparse.ArgumentParser(description="Blogifying script")
parser.add_argument("-f", "--file", type=str, help="Converted markdown to blogify")
parser.add_argument("-a", "--authors", nargs="+", default=[], help="Blog authors")
parser.add_argument("-d", "--date", type=valid_date, help="Blog date in YYYY-MM-DD format")
parser.add_argument("-b", "--blog-title", type=str, help="Blog title")
parser.add_argument("-p", "--page-link", type=str, help="Page link for blog")
parser.add_argument("-s", "--summary", type=str, help="Summary text for blog")
args = parser.parse_args()
args.authors = ", ".join(args.authors)

def convert_md_to_html(input_file, output_file):
    res = subprocess.run(['pandoc', input_file, '-o', output_file], capture_output=True, text=True)
    if res.returncode != 0:
        print(f"Conversion failed: {res.stderr}")
        return None

converted_file = os.path.join(os.path.dirname(args.file), f"converted.html") 
convert_md_to_html(args.file, converted_file)

HEAD_TEXT = f"""<head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <meta name="description" content="sid sharma's blog" />

    <title>{args.blog_title}</title>

    <link rel="icon" type="image/svg+xml" href="/images/favicon.svg">

    <link rel="stylesheet" href="../../styles.css" />
    <link rel="stylesheet" href="../../prism.css" />
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Lora&family=Space+Mono&display=swap" rel="stylesheet">
</head>
"""

PREAMBLE = f"""<div id="preamble">
        <a href="{args.page_link}.html">
            <h1 class="title">{args.blog_title}</h1>
        </a>
        <div class="authors">
            {args.authors}
            <span style="float: right;">
                [{args.date}]
            </span>
        </div>
        <hr>
    </div>
"""

if args.summary:
    SUMMARY = f"""<p>
       {args.summary}
    </p>
"""

with open(converted_file, 'r') as f:
    BLOG_CONTENT = f.read()

FOOTER = """<footer>
        <hr>
        <div class="footer">
            <span style="float: left">
                <a href="/index.html">home</a>
            </span>
            sid's ramblings
        </div>
    </footer>
"""

TEMPLATE = f"""<!DOCTYPE html>
<html lang="en">

{HEAD_TEXT}
<body>
{PREAMBLE}
{SUMMARY if args.summary else ""}
<hr style="border-top: 1px dotted">
{BLOG_CONTENT}
{FOOTER}
</body>
</html>
"""

generated_path = os.path.join(os.path.dirname(args.file), f"{args.page_link}.html")
with open(generated_path, "w") as file:
    file.write(TEMPLATE)
