from common.aliases import AudioCodecChoices, AudioCodecFormats


def get_codecs_to_download(
    audio_codec_choices: AudioCodecChoices,
    audio_codec_formats: AudioCodecFormats,
) -> list[str]:
    codecs_to_download: list[str] = []

    if audio_codec_choices['lossy'] and audio_codec_formats['lossy'] is not None:
        codecs_to_download.append(audio_codec_formats['lossy'])

    if (
        not audio_codec_choices['no_lossless']
        and audio_codec_formats['lossless'] is not None
    ):
        codecs_to_download.append(audio_codec_formats['lossless'])

    if (
        not audio_codec_choices['no_lossless']
        and not audio_codec_choices['lossy']
        and audio_codec_formats['lossless'] is None
        and audio_codec_formats['lossy'] is not None
    ):
        print(
            'Lossless codec option not found in album page, falling back to Lossy codec.'
        )
        codecs_to_download.append(audio_codec_formats['lossy'])

    return codecs_to_download
