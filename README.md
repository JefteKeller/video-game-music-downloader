# Video Game Music Downloader

## Usage

``` Shell
python video_game_music_downloader.py [-h] --url URL -o OUTPUT_PATH [-f] [-ls] [-nl] [-oi] [-ni]
```

### Options

URL to the page where the album is published

``` Shell
--url URL
```

Output directory for the downloaded files

``` Shell
-o, --output-path OUTPUT_PATH
```

Load song links from the backup json file: `link_list.json` instead of the album page url, in case of download errors.

``` Shell
-f, --load-from-file
```

Download the lossy codec option for the songs. Default option if `--no-lossless` is used

``` Shell
-ls, --lossy
```

Disable download of the lossless codec option, if available for the songs

``` Shell
-nl, --no-lossless
```

Only download images from the album

``` Shell
-oi, --only-images
```

Disable download of images from the album

``` Shell
-ni, --no-images
```

Show a help message and exit

``` Shell
-h, --help
```

### Install Dependencies

``` Shell
python -m pip install -r requirements.txt
```
