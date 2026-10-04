# CLAUDE.md

Read `README.md` first for what this is and how it is deployed.

## Invariants

`index.html` is the whole application and must stay that way: one file, no
build step, no package manager, no runtime dependency, and **no external
request of any kind** — no CDN script, no Google Font, no favicon service, no
icon library. Icons are hand-written inline SVG in the `ICONS` map.

This is not stylistic. The page is opened on every new tab, and the entire
design goal is that it costs nothing to open. A single external subresource
reintroduces DNS, TCP and TLS on a path that currently has none, and does it
before the page can become interactive. Reach for a library and you have
defeated the only requirement that matters.

Scripts are inline by necessity too, which means the page cannot be hosted
anywhere that imposes a `script-src` policy without `unsafe-inline`.

## Interactivity is ordered, not incidental

The page must be typeable before it finishes building. Two things make that
true, and both are load-bearing:

- The search input carries `autofocus`, so the caret is placed during parsing
  rather than after the ~500-line script runs. Keystrokes buffered while the
  main thread is blocked then land in the input.
- The theme is applied by a small script in `<head>`, before the body parses.
  Deciding it later paints the dark `:root` defaults first and flashes on the
  way to light.

Do not move either one later in the document, and do not make the page claim
focus unconditionally — the guard on `document.hasFocus()` exists so the page
cannot yank focus out of the browser's address bar mid-word, which splits a
half-typed query across two places.

## Service worker

`sw.js` serves the navigation from cache and revalidates in the background.

- Bump `CACHE` when the worker's own logic or its file list changes. Page edits
  do not need it; the revalidate handles those.
- The background refetch uses `cache: 'reload'` deliberately. A plain `fetch`
  goes through the HTTP cache and, inside the host's `max-age` window, re-reads
  the same stale copy — the worker would look like it was updating and silently
  never would.
- The `fetch` handler must stay scoped to `event.request.mode === 'navigate'`.
  Everything else falls through to the network on purpose: `checkLiveness()`
  probes whether a host is up *right now*, and served from cache it would
  report a stale "online" forever instead of failing visibly.

When debugging anything cache-shaped, `shift`-reload bypasses the worker.

## Geometry

`body` has `zoom: 1.5`, which splits coordinate systems: `getBoundingClientRect`
reports visual pixels (× zoom) while scroll offsets and computed lengths are
layout pixels. Do not try to reconcile the two with a zoom factor — the
relationship is not stable across browser versions, and getting it wrong scrolls
by two-thirds of the intended distance, which looks like a card parked half
under the statusline rather than like an error.

Scrolling therefore declares its constraints and lets the engine do the
arithmetic. `scrollFocusedIntoView` is just `scrollIntoView({ block: 'nearest' })`,
and the space the bars occupy is expressed as `scroll-padding-top`/`-bottom` on
**`html`**, set by `syncScrollPadding()` from the bars' `getBoundingClientRect()`.

The element this sits on is the whole point. `html` is outside `body`'s zoom, so
its lengths, the scroll offset and a `getBoundingClientRect()` measurement are
all in the viewport's coordinate space and need no conversion. Putting the same
values in `scroll-margin` on `.link-card` does not work: the cards are inside
the zoom, so their lengths are scaled and the constraint comes out short.
Measuring with `getBoundingClientRect` and acting with `scrollBy` has the same
flaw in a different place.

## Checking a change

There is no test suite. Before committing, confirm the config still parses and
both inline scripts are syntactically valid:

```sh
python3 - <<'PY'
import re, io, json
s = io.open('index.html', encoding='utf-8').read()
json.loads(re.search(r'id="config">(.*?)</script>', s, re.S).group(1))
print('config OK')
PY
```

Extract each `<script>` block and run `node --check` on it — a syntax error in
an inline script is otherwise invisible until the page renders as a styled,
completely dead shell.

Every link `id` should have a matching entry in `ICONS`, or the card silently
falls back to the generic icon.

Then load it through `python3 serve.py` rather than opening the file directly;
`file://` is a different origin, so `localStorage` (theme, frecency) behaves
differently and service workers do not run at all.

## Commits

Straight to `main`, no branch. Tag a restore point (`pre-<thing>`) before a
change that is awkward to undo — particularly anything touching the service
worker, since rolling that back needs a browser-side unregister as well as a
revert.
