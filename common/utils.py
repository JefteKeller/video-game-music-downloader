import argparse
import pathlib

import cloudscraper
import requests
from bs4 import BeautifulSoup

from common.constants import LINK_LIST_FILE_NAME


def gen_argparse() -> argparse.Namespace:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        '--url',
        required=True,
        help='The URL to the page where the album is published.',
    )

    parser.add_argument(
        '-o',
        '--output-path',
        required=True,
        type=pathlib.Path,
        help='Output directory for the downloaded files.',
    )

    parser.add_argument(
        '-f',
        '--load-from-file',
        action='store_true',
        help=(
            f"""Load song links from the backup json file: "{LINK_LIST_FILE_NAME}"
            instead of the album page url, in case of download errors."""
        ),
    )

    parser.add_argument(
        '-ls',
        '--lossy',
        action='store_true',
        help=(
            """Download the lossy codec option for the songs.
               Default option if "--no-lossless" is used."""
        ),
    )

    parser.add_argument(
        '-nl',
        '--no-lossless',
        action='store_true',
        help='Disable download of the lossless codec option available for the songs.',
    )

    parser.add_argument(
        '-oi',
        '--only-images',
        action='store_true',
        help='Only download images from the album.',
    )

    parser.add_argument(
        '-ni',
        '--no-images',
        action='store_true',
        help='Disable download of images from the album.',
    )

    return parser.parse_args()


def make_request(url: str) -> requests.Response:
    scraper = cloudscraper.create_scraper()

    response = scraper.get(url)
    response.raise_for_status()

    return response


def parse_html(html_content: str, html_parser: str = 'html.parser') -> BeautifulSoup:
    return BeautifulSoup(html_content, html_parser)


def get_html_soup(url: str) -> BeautifulSoup:
    response = make_request(url)

    return parse_html(response.text)
