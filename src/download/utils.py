import os

import requests

from common.aliases import DiscNumber
from common.utils import make_request


def download_file(
    url: str,
    name: str,
    output_path: str,
    session: requests.Session,
) -> None:
    print(f'Downloading file: {name}')

    download = make_request(url, session)

    if download.status_code == 200:
        with open(output_path, 'wb') as file:
            file.write(download.content)

    else:
        print(f'Download failed for file: {name}')


def make_song_output_path(
    output_dir: str, disc_number: DiscNumber, name_with_codec: str
) -> str:
    if disc_number is None:
        return os.path.join(output_dir, name_with_codec)

    output_path_with_disc = os.path.join(output_dir, f'Disc {disc_number:02d}')
    os.makedirs(output_path_with_disc, exist_ok=True)

    return os.path.join(output_path_with_disc, name_with_codec)
