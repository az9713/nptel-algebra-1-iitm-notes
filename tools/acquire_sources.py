"""Acquire private source evidence; never publish work/ caption files."""
from __future__ import annotations

import concurrent.futures
import hashlib
import json
import re
import time
from pathlib import Path

import requests
import yt_dlp

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / 'work' / 'sources'


def acquire(entry):
    vid = entry['id']
    target = WORK / f'{vid}.source.json'
    if target.exists():
        return json.loads(target.read_text(encoding='utf-8'))
    options = {'quiet': True, 'no_warnings': True, 'skip_download': True,
               'socket_timeout': 20, 'retries': 2, 'extractor_retries': 2}
    with yt_dlp.YoutubeDL(options) as dl:
        info = dl.extract_info(f'https://www.youtube.com/watch?v={vid}', download=False)
    tracks = info.get('subtitles', {})
    candidates = [(lang, values) for lang, values in tracks.items()
                  if lang.startswith('en') and not lang.startswith('en-en')]
    mode = 'publisher-caption-track; authorship not verified'
    if not candidates:
        candidates = [(lang, values) for lang, values in info.get('automatic_captions', {}).items()
                      if lang in ('en', 'en-orig')]
        mode = 'YouTube automatic captions'
    if not candidates:
        raise RuntimeError(f'No English captions: {vid}')
    candidates.sort(key=lambda p: (not any(v.get('ext') == 'json3' for v in p[1]), p[0]))
    lang, values = candidates[0]
    track = next((v for v in values if v.get('ext') == 'json3'), None)
    if not track:
        raise RuntimeError(f'No json3 representation: {vid}, {lang}')
    caption = WORK / f'{vid}.captions.json'
    if not caption.exists():
        existing = list(WORK.glob(f'{vid}.{lang}.json3'))
        if existing:
            data = existing[0].read_bytes()
        else:
            response = requests.get(track['url'], timeout=40)
            response.raise_for_status()
            data = response.content
        document = json.loads(data)
        assert document.get('events'), f'Empty caption: {vid}'
        caption.write_bytes(data)
    document = json.loads(caption.read_bytes())
    segments = []
    for event in document.get('events', []):
        text = ''.join(s.get('utf8', '') for s in event.get('segs', []))
        text = re.sub(r'\s+', ' ', text).strip()
        if text:
            segments.append({'start': event['tStartMs']/1000,
                             'end': (event['tStartMs']+event.get('dDurationMs', 0))/1000,
                             'text': text})
    record = {'id': vid, 'title': info['title'], 'duration_seconds': info['duration'],
              'upload_date': info.get('upload_date'), 'channel': info.get('channel'),
              'description': info.get('description'), 'caption_language': lang,
              'caption_label': track.get('name'), 'caption_kind': mode,
              'caption_sha256': hashlib.sha256(caption.read_bytes()).hexdigest(),
              'caption_first_second': segments[0]['start'],
              'caption_last_second': segments[-1]['end'], 'segments': segments,
              'retrieved_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}
    target.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')
    lines = [f"[{int(s['start'])//60:02d}:{int(s['start'])%60:02d}] {s['text']}" for s in segments]
    (WORK / f'{vid}.txt').write_text('\n'.join(lines)+'\n', encoding='utf-8')
    return record


def main():
    playlist = json.loads((WORK / 'playlist-original.json').read_text(encoding='utf-8-sig'))
    failures = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        futures = {pool.submit(acquire, e): e for e in playlist['entries']}
        for future in concurrent.futures.as_completed(futures):
            entry = futures[future]
            try:
                r = future.result()
                print(f"OK {r['id']} {r['title']} ({len(r['segments'])} segments)", flush=True)
            except Exception as exc:
                failures.append({'id': entry['id'], 'error': str(exc)})
                print(f"FAILED {entry['id']}: {exc}", flush=True)
    (WORK / 'acquisition-failures.json').write_text(json.dumps(failures, indent=2), encoding='utf-8')
    print(f"ACQUISITION: {len(playlist['entries'])-len(failures)}/{len(playlist['entries'])}", flush=True)


if __name__ == '__main__':
    main()
