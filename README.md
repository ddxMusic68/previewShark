# preview_shark

A small Windows app for reviewing OBS recordings.

## What it does
- Watches a folder for new video recordings.
- Automatically selects and plays a newly detected recording.
- Play/Pause (`Space`)
- Delete (moves to Windows Recycle Bin, `Delete` key)
- Rename
- Previous/next recording (`Up`/`Down` keys)
- Recording list sorted newest first
- Lets you choose your OBS recording folder
- "Default Folder" button saves the current folder to `settings.json`
- Projects folder: pick your output root, then "Save to Project" moves the
  current recording into a folder you choose or create inside it
- Saving a recording that still looks auto-generated (its name contains a
  `YYYY-MM-DD` date or `(recording)`) shows a warning with a "Do not ask again"
  option

## Run
Install Python 3.11+ on Windows, then:

    py -m pip install -r requirements.txt
    py main.py

## Recommended OBS setup
In OBS, open:
Settings -> Output -> Recording
and choose your Recording Path.

Then choose that same folder in preview_shark.

## Notes
Windows Media Foundation determines which codecs can play in the preview.
If you record to MKV and the preview doesn't play, use OBS's File -> Remux Recordings
to MP4, or configure OBS to automatically remux recordings.
