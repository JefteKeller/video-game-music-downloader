import os

from src import (
    download_album_images_from_page,
    download_songs_from_list,
    gen_argparse,
    get_album_name_from_page,
    get_info_from_page,
)


def main() -> None:
    args = gen_argparse()
    album_name = get_album_name_from_page(args.url)

    output_dir = os.path.join(args.output_path, album_name)
    os.makedirs(output_dir)

    if not args.no_images:
        download_album_images_from_page(args.url, output_dir)

        if args.only_images:
            return print(
                f'\nImages from album: "{album_name}" downloaded to "{args.output_path}" successfully!'
            )

    song_links = get_info_from_page(
        args.url, args.load_from_file, args.lossy, args.no_lossless
    )

    download_songs_from_list(song_links, output_dir)

    return print(
        f'\nAlbum: "{album_name}" downloaded to "{args.output_path}" successfully!'
    )


if __name__ == '__main__':
    main()
