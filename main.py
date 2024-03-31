import os
import pathlib

import json
import argparse

import requests
from bs4 import BeautifulSoup

from typing import Final, TypedDict


PAGE_PREFIX: Final = 'https://downloads.khinsider.com'
LINK_LIST_FILE_NAME: Final = 'link_list.json'
DEFAULT_AUDIO_CODECS: Final = ['mp3', 'flac']

HEADERS: Final = {'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X)'}


class SongInfo(TypedDict):
    name: str
    page_url: str


class SongLink(TypedDict):
    name: str
    mp3_url: str | None
    flac_url: str | None


type SongInfoList = list[SongInfo]
type SongLinkList = list[SongLink]


def make_request(
    url: str, session: requests.Session | None = None, headers: dict[str, str] = HEADERS
):
    if session:
        response = session.get(url, headers=headers)
    else:
        response = requests.get(url, headers=headers)

    response.raise_for_status()

    return response


def parse_html(html_content: str, html_parser: str = 'html.parser'):
    return BeautifulSoup(html_content, html_parser)


def get_song_info_from_page(url: str) -> tuple[SongInfoList, str]:
    song_info_list: SongInfoList = []
    album_name: str = ''

    response = make_request(url)
    html_soup = parse_html(response.text)

    try:
        file_table = html_soup.find(id='songlist').contents
    except AttributeError as e:
        raise AttributeError(
            'The album information could not be found in the requested page'
        ) from e

    try:
        album_name = html_soup.find(id='pageContent').find('h2').text.replace(':', ' -')
    except AttributeError:
        album_name = url.split('/').pop()

    for line in file_table:
        try:
            if line == '\n' or len(line.attrs) > 0:
                continue

            song_info_link = line.find('a')

            song_info: SongInfo = {
                'name': song_info_link.text,
                'page_url': PAGE_PREFIX + song_info_link.attrs['href'],
            }
            song_info_list.append(song_info)

        except (AttributeError, KeyError) as e:
            raise AttributeError('The song download link could not be found') from e

    return song_info_list, album_name


def get_song_link_from_pages(
    song_list: SongInfoList, audio_codecs: list[str]
) -> SongLinkList:

    song_link_list: SongLinkList = []

    song_link_list = []

    with requests.Session() as session:
        for idx, song in enumerate(song_list, start=1):
            response = make_request(song['page_url'], session)
            html_soup = parse_html(response.text)

            anchor_links = html_soup.find_all(class_='songDownloadLink')

            song_mp3_url = None
            song_flac_url = None

            try:
                if len(anchor_links) > 0 and 'mp3' in audio_codecs:
                    song_mp3_url = anchor_links[0].parent.attrs['href']

                if len(anchor_links) > 1 and 'flac' in audio_codecs:
                    song_flac_url = anchor_links[1].parent.attrs['href']

            except (AttributeError, KeyError) as e:
                raise AttributeError(
                    'The song download link could not be retrieved'
                ) from e

            song_link: SongLink = {
                'name': f'{idx:02d}. {song["name"]}',
                'mp3_url': song_mp3_url,
                'flac_url': song_flac_url,
            }

            song_link_list.append(song_link)

    with open(LINK_LIST_FILE_NAME, 'w') as file:
        json.dump(song_link_list, file, indent=4)

    return song_link_list


def download_songs_from_list(
    song_list: SongLinkList, audio_codecs: list[str], output_dir: str
):
    with requests.Session() as session:
        for song in song_list:
            for codec in audio_codecs:
                song_url = song[f'{codec}_url']

                if song_url is None:
                    continue

                print(f'Downloading file: {song["name"]}.{codec}')

                song_download = make_request(song_url, session)

                if song_download.status_code == 200:
                    with open(f'{output_dir}/{song["name"]}.{codec}', 'wb') as file:
                        file.write(song_download.content)

                else:
                    print(f'Download failed for file: {song["name"]}.{codec}')


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        'album_page_url',
        help='The URL to the page where the album is published',
    )

    parser.add_argument(
        '-f',
        '--load-from-file',
        action='store_true',
        help=f'Load song links from the backup json file: "{LINK_LIST_FILE_NAME}" instead of the album page url, in case of download errors',
    )

    parser.add_argument(
        '-o',
        '--output-path',
        default='downloads/',
        type=pathlib.Path,
        help='Output directory for the downloaded files. Default: "%(default)s"',
    )

    parser.add_argument(
        '-c',
        '--codec',
        nargs=1,
        dest='audio_codecs',
        choices=DEFAULT_AUDIO_CODECS,
        default=DEFAULT_AUDIO_CODECS,
        help='Specify a single audio codec to be downloaded. Default: %(default)s -- Important: Codec must be available in the album',
    )

    args = parser.parse_args()

    album_name: str = ''
    song_links: SongLinkList = []

    if args.load_from_file:
        album_name = args.album_page_url.split('/').pop()

        with open(LINK_LIST_FILE_NAME, 'r') as file:
            song_links = json.load(file)

    else:
        song_info_list, album_name = get_song_info_from_page(args.album_page_url)
        song_links = get_song_link_from_pages(song_info_list, args.audio_codecs)

    output_dir = os.path.join(args.output_path, album_name)
    os.makedirs(output_dir)

    download_songs_from_list(song_links, args.audio_codecs, output_dir)

    return print(
        f'Album: "{album_name}" downloaded to the directory: "{args.output_path}" successfully!'
    )


if __name__ == '__main__':
    main()
