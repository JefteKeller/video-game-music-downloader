import os
import pathlib
import urllib.parse

import json
import argparse

import requests
from bs4 import BeautifulSoup

from typing import Final, TypedDict


PAGE_PREFIX: Final = 'https://downloads.khinsider.com'
LINK_LIST_FILE_NAME: Final = 'link_list.json'

HEADERS: Final = {'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X)'}

LOSSY_AUDIO_CODECS: Final = ['mp3']
LOSSLESS_AUDIO_CODECS: Final = ['ogg', 'm4a', 'flac']

AUDIO_CODECS_OPTIONS: Final = LOSSY_AUDIO_CODECS + LOSSLESS_AUDIO_CODECS
AUDIO_CODECS_DEFAULT: Final = ['mp3', 'flac']


type DiscNumber = int | None


class SongInfo(TypedDict):
    disc_number: DiscNumber
    song_number: int | None
    name: str
    page_url: str


class SongLink(TypedDict):
    disc_number: DiscNumber
    name_with_codec: str
    url: str


type SongInfoList = list[SongInfo]
type SongLinkList = list[SongLink]
type SongDownloadList = list[SongLinkList]


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

    print('\nRetrieving Album information...')

    response = make_request(url)
    html_soup = parse_html(response.text)

    try:
        album_name = html_soup.find(id='pageContent').find('h2').text.replace(':', ' -')
    except AttributeError:
        album_name = url.split('/').pop()

    print(f'\nAlbum name: {album_name}')

    try:
        table_header = html_soup.find(id='songlist_header')

        disc_number_header = table_header.find(string='CD')
        song_number_header = table_header.find(string='#')

        for line in html_soup.find(id='songlist').contents:
            if line == '\n' or len(line.attrs) > 0:
                continue

            song_disc_number = None
            song_number = None

            if disc_number_header is not None:
                song_disc_number = int(line.contents[3].string)

                if song_number_header is not None:
                    song_number = int(line.contents[5].string[:-1])

            elif song_number_header is not None:
                song_number = int(line.contents[3].string[:-1])

            song_info_link = line.find('a')

            song_info: SongInfo = {
                'disc_number': song_disc_number,
                'song_number': song_number,
                'name': song_info_link.text,
                'page_url': PAGE_PREFIX + song_info_link.attrs['href'],
            }
            song_info_list.append(song_info)

    except (AttributeError, KeyError) as e:
        raise AttributeError(
            'Album information could not be found in the requested page'
        ) from e

    print(f'Number of songs: {len(song_info_list)}')

    return song_info_list, album_name


def get_song_link_from_pages(
    song_list: SongInfoList, audio_codecs: list[str]
) -> SongDownloadList:

    song_download_list: SongDownloadList = []

    print(f'\nRetrieving download links for songs with codecs: {audio_codecs}')
    print('This may take a while...')

    with requests.Session() as session:
        for idx, song_info in enumerate(song_list, start=1):
            response = make_request(song_info['page_url'], session)
            html_soup = parse_html(response.text)

            anchor_links = html_soup.find_all(class_='songDownloadLink')
            song_links: SongLinkList = []

            song_disc_number = song_info['disc_number']
            song_number = song_info['song_number'] or idx
            song_name = song_info['name']

            song_lossy_link = None
            song_lossless_link = None

            try:
                song_lossy_link = anchor_links[0].parent.attrs['href']

                if len(anchor_links) > 1:
                    song_lossless_link = anchor_links[1].parent.attrs['href']

            except (IndexError, AttributeError, KeyError) as e:
                raise AttributeError(
                    f'The download link for song: "{song_name}" could not be retrieved'
                ) from e

            for codec in audio_codecs:
                song_name_with_codec = f'{song_number:02d}. {song_name}.{codec}'

                if song_lossy_link and codec in LOSSY_AUDIO_CODECS:
                    song: SongLink = {
                        'disc_number': song_disc_number,
                        'name_with_codec': song_name_with_codec,
                        'url': song_lossy_link,
                    }
                    song_links.append(song)

                if song_lossless_link and codec in LOSSLESS_AUDIO_CODECS:
                    song: SongLink = {
                        'disc_number': song_disc_number,
                        'name_with_codec': song_name_with_codec,
                        'url': song_lossless_link,
                    }
                    song_links.append(song)

            song_download_list.append(song_links)

    with open(LINK_LIST_FILE_NAME, 'w') as file:
        json.dump(song_download_list, file, indent=4)

    print(f'Saved download links to file: "{LINK_LIST_FILE_NAME}"')

    return song_download_list


def download_songs_from_list(song_list: SongDownloadList, output_dir: str):
    print('\nDownloading songs...')

    with requests.Session() as session:
        for link_list in song_list:
            for link in link_list:
                url = link['url']
                disc_number = link['disc_number']
                link_name_with_codec = link['name_with_codec']

                if disc_number is not None:
                    song_output_path_with_disc = os.path.join(
                        output_dir, f'Disc {disc_number:02d}'
                    )
                    os.makedirs(song_output_path_with_disc, exist_ok=True)

                    song_output_path = os.path.join(
                        song_output_path_with_disc, link_name_with_codec
                    )
                else:
                    song_output_path = os.path.join(output_dir, link_name_with_codec)

                print(f'Downloading file: {link_name_with_codec}')

                song_download = make_request(url, session)

                if song_download.status_code == 200:
                    with open(song_output_path, 'wb') as file:
                        file.write(song_download.content)

                else:
                    print(f'Download failed for file: {link_name_with_codec}')


def download_album_images_from_page(url: str, output_dir: str) -> None:
    print('\nDownloading Album Images...')

    response = make_request(url)
    html_soup = parse_html(response.text)

    album_images = html_soup.find_all(class_='albumImage')

    with requests.Session() as session:
        for image in album_images:
            image_url = image.a['href']
            url_unquoted = urllib.parse.unquote_plus(image_url)

            image_name = url_unquoted.split('/').pop()
            image_output_path = os.path.join(output_dir, image_name)

            print(f'Downloading image file: {image_name}')

            image_download = make_request(image_url, session)

            if image_download.status_code == 200:
                with open(image_output_path, 'wb') as file:
                    file.write(image_download.content)
            else:
                print(f'Download failed for image file: {image_name}')


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        'album_page_url',
        help='The URL to the page where the album is published',
    )

    parser.add_argument(
        '-ni',
        '--no-images',
        action='store_true',
        help='Disable download of images from the page where the album is published.',
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
        choices=AUDIO_CODECS_OPTIONS,
        default=AUDIO_CODECS_DEFAULT,
        help='Specify a single audio codec to be downloaded. Default: %(default)s -- Important: Codec must be available in the album',
    )

    args = parser.parse_args()

    album_name: str = ''
    song_links: SongDownloadList = []

    if args.load_from_file:
        album_name = args.album_page_url.split('/').pop()

        with open(LINK_LIST_FILE_NAME, 'r') as file:
            song_links = json.load(file)

    else:
        song_info_list, album_name = get_song_info_from_page(args.album_page_url)
        song_links = get_song_link_from_pages(song_info_list, args.audio_codecs)

    output_dir = os.path.join(args.output_path, album_name)
    os.makedirs(output_dir)

    if not args.no_images:
        image_output_dir = os.path.join(output_dir, 'images')
        os.makedirs(image_output_dir)

        download_album_images_from_page(args.album_page_url, image_output_dir)

    download_songs_from_list(song_links, output_dir)

    return print(
        f'\nAlbum: "{album_name}" downloaded to "{args.output_path}" successfully!'
    )


if __name__ == '__main__':
    main()
