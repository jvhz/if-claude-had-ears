/*
 * ears live: read the sound of a browser tab while it plays.
 *
 * Paste this whole file into the page (an AI assistant does this through its
 * browser tool; a person can use the DevTools console). It adds `earsLive`:
 *
 *   earsLive.start()         tap the page's video or audio, silently, and begin collecting
 *   earsLive.status()        how much has been collected so far
 *   earsLive.read()          tempo, key, strongest notes, bass share, loudness curve (small JSON)
 *   earsLive.draw()          cover the page with a picture: loudness, pitch map, notes
 *   earsLive.hide()          take the picture away again
 *   earsLive.stop()          stop collecting
 *   earsLive.transcript()    YouTube only: open the transcript panel and keep its text
 *                            (mutes and pauses the video unless start() is tapping it)
 *   earsLive.text(i)         read that text back, 950 characters at a time (i = 0, 1, 2 ...)
 *
 * It keeps measurements only (how strong each pitch is, 47 times a second).
 * It does not record, save or send the audio anywhere.
 *
 * Two things to know:
 *   - While tapped, the tab is silent on the speakers. Reload the page to get its sound back.
 *   - The browser only lets sound processing start after a real click on the page.
 *     So: start(), click anywhere on the page, then start() again.
 */
(() => {
  const NOTES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'];
  const MAJOR = [6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88];
  const MINOR = [6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17];
  const BANDS = 96;          // one band per semitone, from the C at 32.7 Hz up to about 8 kHz
  const LOWEST = 32.703;
  let E = window.__ears || null;

  async function start() {
    const media = document.querySelector('video,audio');
    if (!media) return 'no video or audio on this page';
    if (!E) {
      const ctx = new (window.AudioContext || window.webkitAudioContext)();
      const source = ctx.createMediaElementSource(media);
      const analyser = ctx.createAnalyser();
      analyser.fftSize = 8192;
      analyser.smoothingTimeConstant = 0;
      const ticker = ctx.createScriptProcessor(1024, 1, 1);   // fires about 47 times a second
      const silent = ctx.createGain();
      silent.gain.value = 0;                                  // nothing reaches the speakers
      source.connect(analyser);
      source.connect(ticker);
      ticker.connect(silent);
      silent.connect(ctx.destination);
      const bins = analyser.frequencyBinCount;
      const spectrum = new Float32Array(bins);
      const bandOf = new Int16Array(bins).fill(-1);
      for (let i = 1; i < bins; i++) {
        const k = Math.round(12 * Math.log2(i * ctx.sampleRate / analyser.fftSize / LOWEST));
        if (k >= 0 && k < BANDS) bandOf[i] = k;
      }
      E = window.__ears = { ctx, media, frames: [], times: [], level: [], on: true };
      ticker.onaudioprocess = (e) => {
        if (media.paused || !E.on) return;
        analyser.getFloatFrequencyData(spectrum);
        const row = new Float32Array(BANDS);
        for (let i = 1; i < bins; i++) {
          const k = bandOf[i];
          if (k >= 0) row[k] += Math.pow(10, spectrum[i] / 10);
        }
        const x = e.inputBuffer.getChannelData(0);
        let sum = 0;
        for (let i = 0; i < x.length; i++) sum += x[i] * x[i];
        E.frames.push(row);
        E.times.push(media.currentTime);
        E.level.push(Math.sqrt(sum / x.length));
      };
    }
    E.on = true;
    await E.ctx.resume().catch(() => {});
    if (E.ctx.state !== 'running') return 'tapped, but waiting for a click on the page. Click, then start() again';
    await media.play().catch(() => {});
    return 'listening from ' + media.currentTime.toFixed(0) + 's' + (media.paused ? ' (the player is paused)' : '');
  }

  function status() {
    if (!E) return 'not started';
    const n = E.frames.length;
    const recent = n ? Math.max(...E.level.slice(-100)) : 0;
    return n + ' readings, ' + (n ? (E.times[n - 1] - E.times[0]).toFixed(1) : 0) + 's collected, player at ' +
      E.media.currentTime.toFixed(1) + 's, ' + (E.media.paused ? 'paused' : 'playing') +
      ', recent level ' + recent.toFixed(3) + (recent === 0 && n > 100 ? ' (silence: this site may block the tap)' : '');
  }

  function stop() { if (E) E.on = false; return status(); }

  function strongest() {
    let top = 0;
    for (const row of E.frames) for (let k = 0; k < BANDS; k++) if (row[k] > top) top = row[k];
    return top || 1e-12;
  }

  function match(a, b) {              // how alike two 12-note profiles are, from -1 to 1
    let ma = 0, mb = 0;
    for (let i = 0; i < 12; i++) { ma += a[i]; mb += b[i]; }
    ma /= 12; mb /= 12;
    let x = 0, y = 0, z = 0;
    for (let i = 0; i < 12; i++) { x += (a[i] - ma) * (b[i] - mb); y += (a[i] - ma) ** 2; z += (b[i] - mb) ** 2; }
    return x / Math.sqrt(y * z + 1e-12);
  }

  function read() {
    if (!E) return 'not started';
    const n = E.frames.length;
    if (n < 200) return 'only ' + n + ' readings so far. ' + status();
    const seconds = E.times[n - 1] - E.times[0];
    const rate = (n - 1) / seconds;
    const top = strongest();

    // Hits: how much the sound jumps up from one reading to the next.
    const hits = new Float32Array(n), before = new Float32Array(BANDS), notes = new Float64Array(12);
    let low = 0, high = 0, all = 0;
    for (let t = 0; t < n; t++) {
      const row = E.frames[t];
      let jump = 0;
      for (let k = 0; k < BANDS; k++) {
        const v = Math.log1p(1e5 * row[k] / top);
        if (t) jump += Math.max(0, v - before[k]);
        before[k] = v;
        if (k >= 12 && k < 72) notes[k % 12] += Math.sqrt(row[k]);
        all += row[k];
        if (k < 35) low += row[k];          // below about 250 Hz
        if (k >= 83) high += row[k];        // above about 4 kHz
      }
      hits[t] = jump;
    }

    // Tempo: the gap at which the hits repeat best, leaning towards 80 to 160 a minute.
    let mean = 0;
    for (let t = 0; t < n; t++) mean += hits[t];
    mean /= n;
    const far = Math.min(n - 1, Math.floor(rate * 8));
    const repeat = new Float32Array(far + 1);
    for (let gap = 0; gap <= far; gap++) {
      let sum = 0;
      for (let t = 0; t + gap < n; t++) sum += (hits[t] - mean) * (hits[t + gap] - mean);
      repeat[gap] = sum;
    }
    const at = (x) => { const i = Math.floor(x), f = x - i; return i + 1 <= far ? (repeat[i] * (1 - f) + repeat[i + 1] * f) / (repeat[0] + 1e-12) : 0; };
    let bpm = 0, best = -9, steadiness = 0;
    for (let b = 50; b <= 210; b += 0.25) {
      const gap = rate * 60 / b;
      if (gap * 4 >= far) continue;
      const fit = (at(gap) + at(2 * gap) + at(3 * gap) + at(4 * gap)) / 4;
      const score = fit * Math.exp(-0.5 * Math.pow(Math.log2(b / 112) / 0.7, 2));
      if (score > best) { best = score; bpm = b; steadiness = fit; }
    }

    // Key: which of the 24 keys the mix of notes fits best.
    const keys = [];
    for (let i = 0; i < 12; i++) {
      keys.push([match(notes, MAJOR.map((_, j) => MAJOR[(j - i + 12) % 12])), NOTES[i] + ' major']);
      keys.push([match(notes, MINOR.map((_, j) => MINOR[(j - i + 12) % 12])), NOTES[i] + ' minor']);
    }
    keys.sort((a, b) => b[0] - a[0]);

    // Loudness, averaged over stretches, 0 = the loudest moment.
    const peak = Math.max(...E.level) || 1e-9;
    const every = seconds > 120 ? 8 : seconds > 40 ? 4 : 2;
    const step = Math.round(rate * every), loud = [];
    for (let t = 0; t + step <= n; t += step) {
      let sum = 0;
      for (let i = t; i < t + step; i++) sum += E.level[i] ** 2;
      loud.push(Math.round(10 * Math.log10(sum / step / peak / peak + 1e-9)));
    }
    const noteTop = Math.max(...notes) || 1;
    return JSON.stringify({
      from: +E.times[0].toFixed(1), to: +E.times[n - 1].toFixed(1), seconds: +seconds.toFixed(1),
      bpm, beat: steadiness >= 0.35 ? 'strong, steady' : steadiness >= 0.2 ? 'clear' : steadiness >= 0.12 ? 'loose' : 'no steady beat',
      also_try_bpm: [bpm / 2, bpm * 2],
      key: keys[0][1], next_best_key: keys[1][1],
      notes: NOTES.map((name, i) => [name, Math.round(100 * notes[i] / noteTop)]).sort((a, b) => b[1] - a[1]).slice(0, 5).map((x) => x.join(':')).join(' '),
      bass_pct: Math.round(100 * low / all), highs_pct: Math.round(100 * high / all),
      ['loud_db_every_' + every + 's']: loud,
    });
  }

  function draw() {
    if (!E || E.frames.length < 50) return 'nothing collected yet';
    const n = E.frames.length, top = strongest();
    let c = document.getElementById('__earsPicture');
    if (!c) {
      c = document.createElement('canvas');
      c.id = '__earsPicture';
      c.style.cssText = 'position:fixed;left:0;top:0;width:100vw;height:100vh;z-index:2147483647;background:#fbfaf7';
      document.documentElement.appendChild(c);
    }
    const W = c.width = 1500, H = c.height = 740, g = c.getContext('2d');
    const left = 90, wide = W - left - 30, t0 = E.times[0], t1 = E.times[n - 1];
    g.fillStyle = '#fbfaf7'; g.fillRect(0, 0, W, H);
    g.fillStyle = '#1b1b1f'; g.font = 'bold 17px sans-serif';
    g.fillText('Live from the browser tab: ' + (t1 - t0).toFixed(0) + ' seconds read while it played', left, 26);
    const label = (text, y) => { g.fillStyle = '#55555c'; g.font = '12px sans-serif'; g.fillText(text, 8, y); };

    // 1. Loudness
    const y1 = 45, h1 = 110, peak = Math.max(...E.level) || 1e-9;
    label('LOUDNESS', y1 + 60);
    g.fillStyle = '#cfcfd6';
    for (let x = 0; x < wide; x++) {
      const a = Math.floor(x / wide * n), b = Math.max(a + 1, Math.floor((x + 1) / wide * n));
      let m = 0;
      for (let i = a; i < b; i++) m = Math.max(m, E.level[i]);
      const y = y1 + h1 * (-Math.max(-50, 20 * Math.log10(m / peak + 1e-9)) / 50);
      g.fillRect(left + x, y, 1, y1 + h1 - y);
    }

    // 2. Pitch map: low at the bottom, high at the top, brighter = stronger
    const y2 = 180, h2 = 330;
    label('PITCH MAP', y2 + 150); label('(low to high)', y2 + 166);
    const img = g.createImageData(wide, h2), scale = Math.log1p(1e5);
    for (let x = 0; x < wide; x++) {
      const row = E.frames[Math.min(n - 1, Math.floor(x / wide * n))];
      for (let y = 0; y < h2; y++) {
        const k = Math.min(BANDS - 1, Math.floor((1 - y / h2) * BANDS));
        const v = Math.log1p(1e5 * row[k] / top) / scale, o = (y * wide + x) * 4;
        img.data[o] = 255 * Math.pow(v, 0.55);
        img.data[o + 1] = 255 * Math.pow(v, 1.9);
        img.data[o + 2] = 255 * (0.45 * Math.sin(Math.PI * v) + 0.15 * v);
        img.data[o + 3] = 255;
      }
    }
    g.putImageData(img, left, y2);

    // 3. Notes: which of the twelve are sounding, darker = stronger
    const y3 = 535, h3 = 168, rowH = h3 / 12;
    label('NOTES', y3 + 80);
    for (let x = 0; x < wide; x += 3) {
      const a = Math.floor(x / wide * n), b = Math.min(n, a + 12), sum = new Float32Array(12);
      for (let i = a; i < b; i++) for (let k = 12; k < 72; k++) sum[k % 12] += Math.sqrt(E.frames[i][k]);
      const m = Math.max(...sum) + 1e-12;
      for (let p = 0; p < 12; p++) {
        const shade = Math.round(251 - 235 * Math.pow(sum[p] / m, 2));
        g.fillStyle = 'rgb(' + shade + ',' + shade + ',' + shade + ')';
        g.fillRect(left + x, y3 + (11 - p) * rowH, 3, rowH - 1);
      }
    }
    g.fillStyle = '#55555c'; g.font = '10px sans-serif';
    for (let p = 0; p < 12; p++) g.fillText(NOTES[p], left - 20, y3 + (11 - p) * rowH + rowH - 3);

    // time marks
    g.font = '12px sans-serif';
    const span = t1 - t0, gap = span > 300 ? 60 : span > 120 ? 20 : span > 45 ? 10 : 5;
    for (let s = 0; s <= span; s += gap) {
      const x = left + wide * s / span, at = t0 + s;
      g.fillStyle = '#55555c';
      g.fillText(Math.floor(at / 60) + ':' + String(Math.floor(at % 60)).padStart(2, '0'), x - 10, H - 12);
      g.fillRect(x, y3 + h3, 1, 5);
    }
    return 'picture drawn: ' + n + ' readings, ' + span.toFixed(1) + 's';
  }

  function hide() { const c = document.getElementById('__earsPicture'); if (c) c.remove(); return 'picture removed'; }

  // YouTube only: the site's own transcript, when the video has one.
  async function transcript() {
    const wait = (ms) => new Promise((r) => setTimeout(r, ms));
    const hush = () => {                       // if we are not tapping the sound, keep the video quiet
      const m = document.querySelector('video');
      if (m && !E) { m.muted = true; m.pause(); }
    };
    hush();
    const expand = document.querySelector('#expand');
    if (expand) expand.click();
    await wait(1200);
    const button = [...document.querySelectorAll('button')].find((b) => /show transcript/i.test(b.innerText || b.getAttribute('aria-label') || ''));
    if (!button) return 'no transcript button: this video may have no captions';
    button.scrollIntoView({ block: 'center' });
    button.click();
    await wait(7000);
    hush();
    const panel = [...document.querySelectorAll('ytd-engagement-panel-section-list-renderer')].filter((p) => p.offsetParent !== null)[0];
    window.__earsText = panel ? panel.innerText.replace(/\n+/g, ' ').replace(/\b\d{1,2}:\d{2}(:\d{2})?\b/g, '').replace(/\s+/g, ' ').trim() : '';
    return window.__earsText.length + ' characters of transcript kept; read it with earsLive.text(0), text(1) ... up to text(' + Math.floor(window.__earsText.length / 950) + ')';
  }

  function text(i) { return (window.__earsText || '').slice(i * 950, (i + 1) * 950); }

  window.earsLive = { start, status, stop, read, draw, hide, transcript, text };
  return 'earsLive ready';
})();
