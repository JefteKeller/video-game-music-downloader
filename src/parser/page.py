import json

import cloudscraper
from pathvalidate import sanitize_filepath

from src.common.aliases import (
    AudioCodecChoices,
    AudioCodecFormats,
    SongDownloadList,
    SongInfoList,
)
from src.common.constants import LINK_LIST_FILE_NAME
from src.common.utils import get_html_soup
from src.parser.album import get_album_info
from src.parser.song import get_song_info_list, get_song_links
from src.parser.utils import get_codecs_to_download


def get_album_name_from_page(url: str) -> str:
    print('\nRetrieving album information...')

    album_name = ''
    html_soup = get_html_soup(url)

    try:
        raw_album_name = (
            html_soup.find(id='pageContent').find('h2').text  # type: ignore
        )
    except AttributeError:
        raw_album_name = url.split('/').pop()

    album_name = sanitize_filepath(raw_album_name)

    print(f'Album name: {album_name}')

    return album_name


def get_album_info_from_page(url: str) -> tuple[SongInfoList, AudioCodecFormats]:
    html_soup = get_html_soup(url)
    album_info = get_album_info(html_soup)

    song_info_list = get_song_info_list(
        html_soup, album_info['disc_number_header'], album_info['song_number_header']
    )

    return song_info_list, album_info['audio_codec_formats']


def get_song_link_from_pages(
    song_list: SongInfoList, codecs_to_download: list[str]
) -> SongDownloadList:
    print(f'\nRetrieving download links for songs with codecs: {codecs_to_download}')
    print('This may take a while...\n')

    song_download_list: SongDownloadList = []

    with cloudscraper.create_scraper() as session:
        for idx, song_info in enumerate(song_list, start=1):
            html_soup = get_html_soup(song_info['page_url'], session)

            anchor_links = html_soup.find_all(class_='songDownloadLink')

            song_links = get_song_links(
                idx, song_info, anchor_links, codecs_to_download
            )
            song_download_list.append(song_links)

    with open(LINK_LIST_FILE_NAME, 'w') as file:
        json.dump(song_download_list, file, indent=4)

    print(f'Saved download links to file: "{LINK_LIST_FILE_NAME}"')

    return song_download_list


def get_info_from_page(
    page_url: str,
    load_links_from_file: bool,
    lossy_codec: bool,
    no_lossless_codec: bool,
) -> SongDownloadList:
    if load_links_from_file:
        with open(LINK_LIST_FILE_NAME, 'r') as file:
            song_links: SongDownloadList = json.load(file)

        return song_links

    song_info_list, audio_codec_formats = get_album_info_from_page(page_url)
    audio_codec_choices: AudioCodecChoices = {
        'lossy': lossy_codec,
        'no_lossless': no_lossless_codec,
    }
    codecs_to_download = get_codecs_to_download(
        audio_codec_choices, audio_codec_formats
    )

    song_links = get_song_link_from_pages(song_info_list, codecs_to_download)

    return song_links
