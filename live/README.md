# ears live: reading sound from a browser tab

`ears.py` needs a file. This is for when there is only a link: a YouTube video, a track on a streaming page, anything that plays in a browser.

`ears_live.js` taps the sound of the tab while it plays and keeps measurements of it. Nothing comes out of the speakers while it is tapped, and no audio is recorded, saved or sent anywhere. Only numbers are kept: how strong each pitch is, about 47 times a second.

## What it gives

- **`earsLive.read()`**: tempo, key, strongest notes, share of bass and highs, and a loudness curve, as a few lines of text.
- **`earsLive.draw()`**: a picture over the page with three rows (loudness, pitch map, notes), to be looked at with a screenshot.
- **`earsLive.transcript()`** (YouTube only): the video's own transcript, which is the reliable way to get what is said.

## How an AI assistant uses it

With a tool that can run JavaScript in the user's browser and take screenshots:

1. Open the link in a new tab.
2. Paste the whole of `ears_live.js` into the page. It answers `earsLive ready`. (Paste the text itself. Fetching the file and running it does not work on YouTube, which blocks that.)
3. Run `await earsLive.start()`. It answers either `listening from ...` or that it is waiting for a click.
4. If it is waiting, click once anywhere on the page (the browser will not start sound processing without a real click), then run `await earsLive.start()` again.
5. Wait for as long as you want to read. It runs in real time: one minute of sound takes one minute.
6. Run `earsLive.status()` to check that readings are arriving and the level is not zero.
7. Run `earsLive.read()` for the numbers.
8. Run `earsLive.draw()` and take a screenshot for the picture. `earsLive.hide()` takes the picture away.
9. Close the tab, or reload it to give the page its sound back.

For speech on YouTube, run `await earsLive.transcript()` and then `earsLive.text(0)`, `earsLive.text(1)` and so on. If the sound is not being tapped, this mutes and pauses the video so it does not play out loud.

## What has been tested

| Test | Result |
|---|---|
| The repo's test track (true answers: 120 bpm, A minor, quiet / build / loud / quiet / loud / fade) | Read 120 bpm and A minor, with the right loudness shape. The picture matched the one `ears.py` draws from the file |
| A YouTube video (with an earlier draft of this script) | Readings arrived at a normal level for 25 seconds, with nothing audible |
| `transcript()` on a YouTube video | 11,510 characters of transcript returned |

## Limits

- **Real time only.** It cannot skip ahead; it reads as the page plays.
- **Less detail than `ears.py`.** No sections, beat times, chords or style clues yet. Those need the file.
- **No words from the sound itself.** Words come from the site's captions. A page without captions gives no words this way.
- **Some sites will give silence.** Sites that protect their audio, or that serve it from another address without permission to read it, hand the tap nothing. `status()` warns when the level stays at zero. Not yet tested: SoundCloud, Spotify.
- **The tab is silent while tapped.** Reload the page to undo it.
