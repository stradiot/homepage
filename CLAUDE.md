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

`body` has `zoom: 1.5`, and that single declaration is behind every scrolling
bug this file has had. It makes two coordinate systems coexist — the zoomed
subtree and the unzoomed root — and browsers do not agree on which one
`getBoundingClientRect` reports for a zoomed element. Any code that measures in
one and acts in the other is guessing, and the symptom is never an exception: it
is a focused card parked slightly under the statusline, which reads as a design
nit rather than a bug.

So: do not measure the bars at runtime, and do not convert between the two
spaces. `scrollFocusedIntoView` is `scrollIntoView({ block: 'nearest' })`, and
the strips the bars cover are static `scroll-padding-top`/`-bottom` on **`html`**.

Two properties make that safe. `html` is outside the zoom, so its lengths share
a coordinate system with the scroll offset — the same values in `scroll-margin`
on `.link-card` do *not* work, because the cards are inside the zoom and come
out scaled. And the values are deliberately too large: both bars are fixed-height
by design, over-reserving only parks a card further from the edge, while
under-reserving hides it. Bump them if a bar grows.

Deleting `zoom` and scaling through a root `font-size` with `rem` units would
retire this whole section. It is the real fix; nobody has done it.

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
