import os
import urllib.parse

import requests

from common.utils import get_html_soup
from download.utils import download_file


def download_album_images_from_page(url: str, output_dir: str) -> None:
    print('\nDownloading album images...\n')

    image_output_dir = os.path.join(output_dir, 'images')
    os.makedirs(image_output_dir)

    html_soup = get_html_soup(url)
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

            image_output_path = os.path.join(image_output_dir, image_name)

            download_file(image_url, session, image_name, image_output_path)
