from src.common.utils import gen_argparse
from src.download.image import download_album_images_from_page
from src.download.song import download_songs_from_list
from src.parser.page import get_album_name_from_page, get_info_from_page

__all__ = [
    'gen_argparse',
    'download_album_images_from_page',
    'download_songs_from_list',
    'get_album_name_from_page',
    'get_info_from_page',
]
