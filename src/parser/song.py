from pathvalidate import sanitize_filename

from src.common.aliases import (
    SongInfo,
    SongInfoList,
    SongLink,
    SongLinkList,
    SongNumbers,
)
from src.common.constants import LOSSLESS_AUDIO_CODECS, LOSSY_AUDIO_CODECS, PAGE_PREFIX


def get_song_numbers(
    info_line, disc_number_header: str | None, song_number_header: str | None
) -> SongNumbers:
    disc_number = None
    song_number = None

    if disc_number_header is not None:
        try:
            disc_number = int(info_line.contents[3].string)
        except TypeError:
            disc_number = None

        if song_number_header is not None:
            try:
                song_number = int(info_line.contents[5].string[:-1])
            except TypeError:
                song_number = None

    elif song_number_header is not None:
        try:
            song_number = int(info_line.contents[3].string[:-1])
        except TypeError:
            song_number = None

    return {
        'disc_number': disc_number,
        'song_number': song_number,
    }


def get_song_info(
    info_line, disc_number_header: str | None, song_number_header: str | None
) -> SongInfo:
    song_numbers = get_song_numbers(info_line, disc_number_header, song_number_header)
    song_info_link = info_line.find('a')

    song_name = sanitize_filename(song_info_link.text)
    page_url = PAGE_PREFIX + song_info_link.attrs['href']

    return {
        **song_numbers,
        'name': song_name,
        'page_url': page_url,
    }


def get_song_info_list(
    html_soup, disc_number_header, song_number_header
) -> SongInfoList:
    song_info_list: SongInfoList = []

    try:
        for line in html_soup.find(id='songlist').contents:
            if line == '\n' or len(line.attrs) > 0:
                continue

            song_info_list.append(
                get_song_info(line, disc_number_header, song_number_header)
            )
    except (AttributeError, KeyError) as e:
        raise AttributeError(
            'Song information could not be found in the requested page'
        ) from e

    return song_info_list


def get_song_links(
    idx: int,
    song_info: SongInfo,
    anchor_links: list,
    codecs_to_download: list[str],
) -> SongLinkList:
    song_links: SongLinkList = []

    song_disc_number = song_info['disc_number']
    song_number = song_info['song_number'] or idx
    song_name = song_info['name']

    song_lossy_link = None
    song_lossless_link = None

    try:
        song_lossy_link = anchor_links[0].parent.attrs['href']

        if len(anchor_links) > 1:
            song_lossless_link = anchor_links[1].parent.attrs['href']

    except (IndexError, AttributeError, KeyError) as e:
        raise AttributeError(
            f"""The download link for song: "{song_info['name']}" could not be retrieved"""
        ) from e

    for codec in codecs_to_download:
        song_url = None

        if codec in LOSSY_AUDIO_CODECS and song_lossy_link is not None:
            song_url = song_lossy_link

        if codec in LOSSLESS_AUDIO_CODECS:
            if song_lossless_link is not None:
                song_url = song_lossless_link
            else:
                print(
                    f'Lossless song url not found, falling back to Lossy for the song: {song_name}.'
                )
                codec = LOSSY_AUDIO_CODECS[0].lower()
                song_url = song_lossy_link

        song: SongLink = {
            'disc_number': song_disc_number,
            'name_with_codec': f'{song_number:02d}. {song_name}.{codec.lower()}',
            'url': song_url,
        }
        song_links.append(song)

    return song_links
