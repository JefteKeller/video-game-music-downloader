import requests
from bs4 import BeautifulSoup


PAGE_URL = None
PAGE_ALBUM_NAME = None
PAGE_PREFIX = 'https://downloads.khinsider.com'
LINK_LIST_FILE_NAME = 'link_list.json'

HEADERS = {'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X)'}


def get_song_info_from_page(page_url):
    global PAGE_ALBUM_NAME

    song_info_list = []

    res_page_html = requests.get(page_url, headers=HEADERS)
    res_page_html.raise_for_status()

    soup = BeautifulSoup(res_page_html.text, 'html.parser')

    file_table = soup.find(id='songlist') or []
    album_title = soup.find(id='pageContent').find('h2')

    if album_title is not None:
        PAGE_ALBUM_NAME = album_title.text.replace(':', ' -')

    for line in file_table.contents:
        if line == '\n' or len(line.attrs) > 0:
            continue

        song_info_link = line.find('a')

        song_name = song_info_link.text
        song_page_url = PAGE_PREFIX + song_info_link.attrs['href']

        song_info = {'name': song_name, 'page_url': song_page_url}
        song_info_list.append(song_info)

    return song_info_list


def get_song_link_from_pages(song_list):
    global LINK_LIST_FILE_NAME

    import json

    song_link_list = []

    with requests.Session() as session:
        for idx, song in enumerate(song_list, start=1):
            res_page_html = session.get(song['page_url'], headers=HEADERS)
            res_page_html.raise_for_status()

            soup = BeautifulSoup(res_page_html.text, 'html.parser')
            anchor_links = soup.find_all(class_='songDownloadLink')

            song_info = {
                'name': f'{idx :02d}. {song["name"]}',
                'mp3_url': None,
                'flac_url': None,
            }

            if len(anchor_links) == 1:
                song_info['mp3_url'] = anchor_links[0].parent.attrs['href']

            if len(anchor_links) == 2:
                song_info['mp3_url'] = anchor_links[0].parent.attrs['href']
                song_info['flac_url'] = anchor_links[1].parent.attrs['href']

            song_link_list.append(song_info)

    with open(LINK_LIST_FILE_NAME, 'w') as file:
        json.dump(song_link_list, file, indent=4)

    return song_link_list


def download_songs_from_list(song_list):
    global PAGE_ALBUM_NAME

    import os

    if PAGE_ALBUM_NAME is None:
        import random
        import string

        PAGE_ALBUM_NAME = ''.join(
            random.choices(string.ascii_letters + string.digits, k=12)
        )

    folder_path = f'/mnt/z/temp/{PAGE_ALBUM_NAME}'
    os.mkdir(folder_path)

    with requests.Session() as session:
        for song in song_list:
            if song['mp3_url'] is not None:
                print(f'Downloading file: {song["name"]}.mp3')

                song_mp3_download = session.get(
                    song['mp3_url'], headers=HEADERS, stream=True
                )

                if song_mp3_download.status_code == 200:
                    with open(f'{folder_path}/{song["name"]}.mp3', 'wb') as file:
                        file.write(song_mp3_download.content)

                else:
                    print(f'Download failed for file: {song["name"]}.mp3')

            if song['flac_url'] is not None:
                print(f'Downloading file: {song["name"]}.flac')

                song_flac_download = session.get(
                    song['flac_url'], headers=HEADERS, stream=True
                )

                if song_flac_download.status_code == 200:
                    with open(f'{folder_path}/{song["name"]}.flac', 'wb') as file:
                        file.write(song_flac_download.content)

                else:
                    print(f'Download failed for file: {song["name"]}.flac')


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument(
        '-f',
        '--filename',
        type=str,
        help='Use a json file to load the links instead of a page url',
    )

    parser.add_argument(
        'page_url',
        type=str,
        help='The URL to the page where the album is published',
    )
    args = parser.parse_args()

    PAGE_URL = args.page_url
    song_links = []

    if PAGE_URL is not None and args.filename is None:
        song_info_list = get_song_info_from_page(PAGE_URL)
        song_links = get_song_link_from_pages(song_info_list)

    if args.filename is not None:
        import json

        with open(args.filename, 'r') as file:
            song_links = json.load(file)

    download_songs_from_list(song_links)
