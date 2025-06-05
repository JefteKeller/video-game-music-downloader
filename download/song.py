import requests

from common.aliases import SongDownloadList
from download.utils import download_file, make_song_output_path


def download_songs_from_list(song_list: SongDownloadList, output_dir: str) -> None:
    print('\nDownloading songs...')

    with requests.Session() as session:
        for link_list in song_list:
            for link in link_list:
                url = link['url']
                disc_number = link['disc_number']
                name_with_codec = link['name_with_codec']

                if url is None:
                    print(
                        f'Download link is invalid for file: {name_with_codec}. Skipping...'
                    )
                    continue

                song_output_path = make_song_output_path(
                    output_dir, disc_number, name_with_codec
                )

                download_file(url, session, name_with_codec, song_output_path)
