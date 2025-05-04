## Kinescoper

This is a simple script that is heavily based on https://github.com/anijackich/kinescope-dl.
The latter does not work for me but it does generate correct decryption keys.

### Installation

[FFmpeg](https://ffmpeg.org/download.html) and [mp4decrypt](https://www.bento4.com/downloads/) are required as
in the kinescope-dl. You will need the `requests` package installed too.

### Running

Simply run `python3 kinescoper.py` with arguments:
- `-u`: The master.m3u8 url. It must look like `https://kinescope.io/11111-1111-111-111-111/master.m3u8?params`
- `-r`: The referer header. Kinescope requires one to be set for embedded installations. Only the site name is required.
E.g. `https://sitename.com/` suits well.
- `-t`: The target file name. I.e. `output.mp4`.

The script currently extracts 720p only. Feel free to adjust.
