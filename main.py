import requests
from bs4 import BeautifulSoup


PAGE_URL = None
PAGE_PREFIX = 'https://downloads.khinsider.com'

HEADERS = {'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X'}


def get_song_info_from_page(page_url):
    song_info_list = []

    res_page_html = requests.get(page_url, headers=HEADERS)
    res_page_html.raise_for_status()

    soup = BeautifulSoup(res_page_html.text, 'html.parser')

    file_table = soup.find(id='songlist') or []

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

    with open('song_link_list.json', 'w') as file:
        json.dump(song_link_list, file, indent=4)

    return song_link_list


def download_songs_from_list(song_list):
    import os
    import random
    import string

    folder_name = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
    os.mkdir(f'./songs/{folder_name}')

    with requests.Session() as session:
        for song in song_list:
            if song['mp3_url'] is not None:
                print(f'Downloading File: {song["name"]}.mp3')

                song_mp3_download = session.get(
                    song['mp3_url'], headers=HEADERS, stream=True
                )

                if song_mp3_download.status_code == 200:
                    with open(
                        f'./songs/{folder_name}/{song["name"]}.mp3', 'wb'
                    ) as file:
                        file.write(song_mp3_download.content)

                else:
                    print(f'Download Failed For File: {song["name"]}.mp3')

            if song['flac_url'] is not None:
                print(f'Downloading File: {song["name"]}.flac')

                song_flac_download = session.get(
                    song['flac_url'], headers=HEADERS, stream=True
                )

                if song_flac_download.status_code == 200:
                    with open(
                        f'./songs/{folder_name}/{song["name"]}.flac', 'wb'
                    ) as file:
                        file.write(song_flac_download.content)

                else:
                    print(f'Download Failed For File: {song["name"]}.flac')


if __name__ == '__main__':
    import sys

    try:
        PAGE_URL = sys.argv[1]

    except IndexError:
        print('The page url is not specified.')

    if PAGE_URL is not None:
        song_info_list = get_song_info_from_page(PAGE_URL)
        song_links = get_song_link_from_pages(song_info_list)

        download_songs_from_list(song_links)
