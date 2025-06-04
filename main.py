import json
import os
import urllib.parse

import requests

from aliases import (
    AudioCodecChoices,
    AudioCodecFormats,
    SongDownloadList,
    SongInfoList,
)
from constants import (
    LINK_LIST_FILE_NAME,
)
from utils import (
    download_image,
    download_song,
    gen_argparse,
    get_album_info,
    get_codecs_to_download,
    get_song_info_list,
    get_song_links,
    make_request,
    parse_html,
)


def get_album_info_from_page(url: str) -> tuple[SongInfoList, str, AudioCodecFormats]:
    print('\nRetrieving Album information...')

    response = make_request(url)
    html_soup = parse_html(response.text)

    album_info = get_album_info(url, html_soup)

    song_info_list = get_song_info_list(
        html_soup, album_info['disc_number_header'], album_info['song_number_header']
    )

    return song_info_list, album_info['album_name'], album_info['audio_codec_formats']


def get_song_link_from_pages(
    song_list: SongInfoList, codecs_to_download: list[str]
) -> SongDownloadList:
    print(f'\nRetrieving download links for songs with codecs: {codecs_to_download}')
    print('This may take a while...')

    song_download_list: SongDownloadList = []

    with requests.Session() as session:
        for idx, song_info in enumerate(song_list, start=1):
            response = make_request(song_info['page_url'], session)
            html_soup = parse_html(response.text)

            anchor_links = html_soup.find_all(class_='songDownloadLink')

            song_links = get_song_links(
                idx, song_info, anchor_links, codecs_to_download
            )
            song_download_list.append(song_links)

    with open(LINK_LIST_FILE_NAME, 'w') as file:
        json.dump(song_download_list, file, indent=4)

    print(f'Saved download links to file: "{LINK_LIST_FILE_NAME}"')

    return song_download_list


def download_songs_from_list(song_list: SongDownloadList, output_dir: str) -> None:
    print('\nDownloading songs...')

    with requests.Session() as session:
        for link_list in song_list:
            for link in link_list:
                url = link['url']
                disc_number = link['disc_number']
                link_name_with_codec = link['name_with_codec']

                if url is None:
                    print(
                        f'Download link is invalid for file: {link_name_with_codec}. Skipping...'
                    )
                    continue

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

                download_song(url, session, link_name_with_codec, song_output_path)


def download_album_images_from_page(url: str, output_dir: str) -> None:
    print('\nDownloading Album Images...')

    response = make_request(url)
    html_soup = parse_html(response.text)

    album_images = html_soup.find_all(class_='albumImage')

    with requests.Session() as session:
        for image in album_images:
            image_url = None
            try:
                image_url = image.a['href']
            except (AttributeError, KeyError):
                print('Image link is invalid. Skipping...')
                continue

            if not image_url:
                continue

            url_unquoted = urllib.parse.unquote_plus(image_url)
            image_name = url_unquoted.split('/').pop()

            image_output_path = os.path.join(output_dir, image_name)

            download_image(image_url, session, image_name, image_output_path)


def main() -> None:
    args = gen_argparse()

    album_name = ''
    song_links: SongDownloadList = []

    if args.load_from_file:
        album_name = args.album_page_url.split('/').pop()

        with open(LINK_LIST_FILE_NAME, 'r') as file:
            song_links = json.load(file)

    else:
        song_info_list, album_name, audio_codec_formats = get_album_info_from_page(
            args.album_page_url
        )
        audio_codec_choices: AudioCodecChoices = {
            'lossy': args.lossy,
            'no_lossless': args.no_lossless,
        }
        codecs_to_download = get_codecs_to_download(
            audio_codec_choices, audio_codec_formats
        )

        song_links = get_song_link_from_pages(song_info_list, codecs_to_download)

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
