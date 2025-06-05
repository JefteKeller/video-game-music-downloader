import os
from parser.page import get_info_from_page

from common.utils import gen_argparse
from download.image import download_album_images_from_page
from download.song import download_songs_from_list


def main() -> None:
    args = gen_argparse()

    album_name, song_links = get_info_from_page(
        args.album_page_url, args.load_from_file, args.lossy, args.no_lossless
    )

    output_dir = os.path.join(args.output_path, album_name)
    os.makedirs(output_dir)

    if not args.no_images:
        download_album_images_from_page(args.album_page_url, output_dir)

    download_songs_from_list(song_links, output_dir)

    return print(
        f'\nAlbum: "{album_name}" downloaded to "{args.output_path}" successfully!'
    )


if __name__ == '__main__':
    main()
