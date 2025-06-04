import argparse
import pathlib

import requests
from bs4 import BeautifulSoup

from aliases import (
    AlbumInfo,
    AudioCodecChoices,
    AudioCodecFormats,
    SongInfo,
    SongInfoList,
    SongLink,
    SongLinkList,
)
from constants import (
    HEADERS,
    LINK_LIST_FILE_NAME,
    LOSSLESS_AUDIO_CODECS,
    LOSSY_AUDIO_CODECS,
    PAGE_PREFIX,
)


def gen_argparse() -> argparse.Namespace:
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
        help=(
            f"""Load song links from the backup json file: "{LINK_LIST_FILE_NAME}"
            instead of the album page url, in case of download errors."""
        ),
    )

    parser.add_argument(
        '-o',
        '--output-path',
        default='downloads/',
        type=pathlib.Path,
        help='Output directory for the downloaded files. Default: "%(default)s"',
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

    return parser.parse_args()


def make_request(
    url: str, session: requests.Session | None = None, headers: dict[str, str] = HEADERS
) -> requests.Response:
    if session:
        response = session.get(url, headers=headers)
    else:
        response = requests.get(url, headers=headers)

    response.raise_for_status()

    return response


def parse_html(html_content: str, html_parser: str = 'html.parser') -> BeautifulSoup:
    return BeautifulSoup(html_content, html_parser)


def get_album_info(url, html_soup) -> AlbumInfo:
    album_name = ''

    try:
        album_name = html_soup.find(id='pageContent').find('h2').text.replace(':', ' -')
    except AttributeError:
        album_name = url.split('/').pop()

    print(f'\nAlbum name: {album_name}')

    table_header = html_soup.find(id='songlist_header')

    disc_number_header = table_header.find(string='CD')
    song_number_header = table_header.find(string='#')

    audio_codec_formats: AudioCodecFormats = {
        'lossy': table_header.find(string=LOSSY_AUDIO_CODECS),
        'lossless': table_header.find(string=LOSSLESS_AUDIO_CODECS),
    }

    return {
        'album_name': album_name,
        'disc_number_header': disc_number_header,
        'song_number_header': song_number_header,
        'audio_codec_formats': audio_codec_formats,
    }


def get_song_info(
    info_line, disc_number_header: str | None, song_number_header: str | None
) -> SongInfo:
    song_disc_number = None
    song_number = None

    if disc_number_header is not None:
        song_disc_number = int(info_line.contents[3].string)

        if song_number_header is not None:
            song_number = int(info_line.contents[5].string[:-1])

    elif song_number_header is not None:
        song_number = int(info_line.contents[3].string[:-1])

    song_info_link = info_line.find('a')

    return {
        'disc_number': song_disc_number,
        'song_number': song_number,
        'name': song_info_link.text,
        'page_url': PAGE_PREFIX + song_info_link.attrs['href'],
    }


def get_song_info_list(
    html_soup, disc_number_header, song_number_header
) -> SongInfoList:
    song_info_list: SongInfoList = []

    try:
        for line in html_soup.find(id='songlist').contents:
            if line == '\n' or len(line.attrs) > 0:
                continue

            song_info_list.append(
                get_song_info(line, disc_number_header, song_number_header)
            )
    except (AttributeError, KeyError) as e:
        raise AttributeError(
            'Song information could not be found in the requested page'
        ) from e

    print(f'Number of songs: {len(song_info_list)}')

    return song_info_list


def get_codecs_to_download(
    audio_codec_choices: AudioCodecChoices,
    audio_codec_formats: AudioCodecFormats,
) -> list[str]:
    codecs_to_download: list[str] = []

    if audio_codec_choices['lossy'] and audio_codec_formats['lossy'] is not None:
        codecs_to_download.append(audio_codec_formats['lossy'])

    if (
        not audio_codec_choices['no_lossless']
        and audio_codec_formats['lossless'] is not None
    ):
        codecs_to_download.append(audio_codec_formats['lossless'])

    if (
        not audio_codec_choices['no_lossless']
        and not audio_codec_choices['lossy']
        and audio_codec_formats['lossless'] is None
        and audio_codec_formats['lossy'] is not None
    ):
        print(
            'Lossless codec option not found in album page, falling back to Lossy codec.'
        )
        codecs_to_download.append(audio_codec_formats['lossy'])

    return codecs_to_download


def get_song_links(
    idx: int,
    song_info: SongInfo,
    anchor_links: list,
    codecs_to_download: list[str],
) -> SongLinkList:
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
            f"""The download link for song: "{song_info['name']}" could not be retrieved"""
        ) from e

    for codec in codecs_to_download:
        song_url = None

        if codec in LOSSY_AUDIO_CODECS and song_lossy_link is not None:
            song_url = song_lossy_link

        if codec in LOSSLESS_AUDIO_CODECS:
            if song_lossless_link is not None:
                song_url = song_lossless_link
            else:
                print(
                    f'Lossless song url not found, falling back to Lossy for the song: {song_name}.'
                )
                codec = LOSSY_AUDIO_CODECS[0].lower()
                song_url = song_lossy_link

        song: SongLink = {
            'disc_number': song_disc_number,
            'name_with_codec': f'{song_number:02d}. {song_name}.{codec.lower()}',
            'url': song_url,
        }
        song_links.append(song)

    return song_links


def download_song(
    url: str,
    session: requests.Session,
    link_name_with_codec: str,
    song_output_path: str,
) -> None:
    print(f'Downloading file: {link_name_with_codec}')

    song_download = make_request(url, session)

    if song_download.status_code == 200:
        with open(song_output_path, 'wb') as file:
            file.write(song_download.content)

    else:
        print(f'Download failed for file: {link_name_with_codec}')


def download_image(
    url: str,
    session: requests.Session,
    image_name: str,
    image_output_path: str,
) -> None:
    print(f'Downloading image file: {image_name}')

    image_download = make_request(url, session)

    if image_download.status_code == 200:
        with open(image_output_path, 'wb') as file:
            file.write(image_download.content)
    else:
        print(f'Download failed for image file: {image_name}')
