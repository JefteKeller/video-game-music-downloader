from typing import TypedDict


class AudioCodecChoices(TypedDict):
    lossy: bool
    no_lossless: bool


class AudioCodecFormats(TypedDict):
    lossy: str | None
    lossless: str | None


class AlbumInfo(TypedDict):
    disc_number_header: str | None
    song_number_header: str | None
    audio_codec_formats: AudioCodecFormats


type DiscNumber = int | None


class SongNumbers(TypedDict):
    disc_number: DiscNumber
    song_number: int | None


class SongInfo(SongNumbers):
    name: str
    page_url: str


class SongLink(TypedDict):
    disc_number: DiscNumber
    name_with_codec: str
    url: str | None


type SongInfoList = list[SongInfo]
type SongLinkList = list[SongLink]
type SongDownloadList = list[SongLinkList]
