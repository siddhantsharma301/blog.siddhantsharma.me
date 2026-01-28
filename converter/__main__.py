"""CLI entry point for blog converter."""

import argparse
import sys

from . import post, travel


def main():
    parser = argparse.ArgumentParser(
        prog='blog',
        description='Blog converter - markdown to HTML'
    )
    subparsers = parser.add_subparsers(dest='command', required=True)

    # post subcommand
    post_parser = subparsers.add_parser('post', help='Convert a markdown file to HTML')
    post_parser.add_argument('file', help='Markdown file to convert')
    post_parser.add_argument('-o', '--output', help='Output HTML file')
    post_parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')

    # travel subcommand
    travel_parser = subparsers.add_parser('travel', help='Build the travel lore page')
    travel_parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')

    args = parser.parse_args()

    if args.command == 'post':
        try:
            post.convert(args.file, output=args.output, verbose=args.verbose)
        except FileNotFoundError as e:
            print(f"Error: {e}")
            sys.exit(1)
    elif args.command == 'travel':
        travel.build(verbose=args.verbose)


if __name__ == '__main__':
    main()
