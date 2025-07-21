from src.common.aliases import AlbumInfo, AudioCodecFormats
from src.common.constants import LOSSLESS_AUDIO_CODECS, LOSSY_AUDIO_CODECS


def get_album_info(html_soup) -> AlbumInfo:
    table_header = html_soup.find(id='songlist_header')

    disc_number_header = table_header.find(string='CD')
    song_number_header = table_header.find(string='#')

    audio_codec_formats: AudioCodecFormats = {
        'lossy': table_header.find(string=LOSSY_AUDIO_CODECS),
        'lossless': table_header.find(string=LOSSLESS_AUDIO_CODECS),
    }

    return {
        'disc_number_header': disc_number_header,
        'song_number_header': song_number_header,
        'audio_codec_formats': audio_codec_formats,
    }
