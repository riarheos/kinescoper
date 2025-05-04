import argparse
import base64
import os
import subprocess

import requests


class Kinescoper:
    url: str

    def __init__(self):
        self.url, self.referer, self.target = self._get_args()

        self.session = requests.Session()
        self.session.headers.update({'Referer': self.referer})
        self.key_cache = {}

        self.video_m3u8, self.audio_m3u8 = self._process_master_m3u8()

        self._process_m3u8(self.video_m3u8, 'video.mp4')
        self._process_m3u8(self.audio_m3u8, 'audio.mp4')
        self._finalize('video.mp4', 'audio.mp4', self.target)

    @staticmethod
    def _get_args():
        parser = argparse.ArgumentParser()
        parser.add_argument('-u', '--url', help='Master M3U8 URL', required=True)
        parser.add_argument('-r', '--referer', help='Referer', required=True)
        parser.add_argument('-t', '--target', help='Target file', required=True)
        args = parser.parse_args()
        return args.url, args.referer, args.target

    def _process_master_m3u8(self):
        print('Getting master m3u8')
        data = self.session.get(self.url)
        m3u8 = data.text

        for line in m3u8.splitlines():
            if line.startswith('#EXT-X-MEDIA:TYPE=AUDIO'):
                audio = line.split('"')[-2]
                continue

            if not line.startswith('#') and line.find('720') != -1:
                video = line.strip()
                continue

        idx = self.url.split('?')[0].rfind('/')
        prefix = self.url[:idx+1]

        return prefix + video, prefix + audio

    def _get_encryption_key(self, pre_key: str) -> str:
        if pre_key in self.key_cache:
            return self.key_cache[pre_key]

        print(f'Getting encryption key for {pre_key}')
        pre_key_bytes = bytes.fromhex(pre_key)
        b64 = base64.b64encode(pre_key_bytes).decode().replace('=', '')

        video_id = self.url.split('/')[3]
        r = self.session.post(f'https://license.kinescope.io/v1/vod/{video_id}/acquire/clearkey?token=',
                              headers={'Origin': 'https://kinescope.io'},
                              json={
                                  'kids': [b64],
                                  'type': 'temporary'
                              })
        key = base64.b64decode(r.json()['keys'][0]['k'] + '==').hex()
        self.key_cache[pre_key] = key
        return key

    def _process_m3u8(self, url: str, tgt: str):
        print('Getting urls from ' + url)

        data = self.session.get(url)
        m3u8 = data.text

        idx = 0
        prev = ''
        file_enc = tgt + '.enc'
        with open(file_enc, 'wb') as fenc:
            for line in m3u8.splitlines():
                if line.startswith('#EXT-X-KEY:METHOD=SAMPLE-AES'):
                    pre_key = line.split('"')[1].split('?')[0].split('/')[-1]
                    key = self._get_encryption_key(pre_key)
                    continue

                if line.startswith('#'):
                    continue

                if line != prev:
                    prev = line
                    idx += 1

                    print(f'Downloading file {idx}')
                    r = self.session.get(line, stream=True)
                    for chunk in r.iter_content(1024):
                        fenc.write(chunk)

        print(f'Decoding file')
        subprocess.check_call(['mp4decrypt', '--key', f'1:{key}', file_enc, tgt])

        print('Cleaning up')
        os.remove(file_enc)

    def _finalize(self, video: str, audio: str, out: str):
        print('Finalizing')
        subprocess.check_call(['ffmpeg', '-i', video, '-i', audio, '-c', 'copy', out])

        print('Cleaning up')
        os.remove(video)
        os.remove(audio)
        

if __name__ == '__main__':
    Kinescoper()
