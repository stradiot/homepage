# homepage

A keyboard-driven browser new tab page. One self-contained HTML file: no build
step, no dependencies, and no external requests at runtime — no fonts, no CDN,
no icon service. Everything, including the link config and all SVG icons, is
inline in `index.html`.

Live at <https://stradiot.github.io/homepage/>.

## Using it

Search is focused on open, so you can type immediately. A query filters the
link cards; if nothing matches, Enter sends it to the search engine. Anything
that looks like a URL, a bare hostname or an IP address is opened directly
instead of searched — private-range addresses over `http`, everything else over
`https`, since LAN boxes rarely speak TLS.

| key | action |
| --- | --- |
| `/` | focus search |
| `esc` | clear search, then drop into grid navigation |
| `h` `j` `k` `l` / arrows | move around the grid |
| `g` `g` / `G` | first / last card |
| `↵` | open focused link (`⌘↵` in a new tab) |
| `t` | toggle theme |
| `?` | keybind help |

Cards are ordered within each category by frecency — visit count decayed over
roughly 30 days, so the ordering tracks current habits rather than ossifying
around old peaks. Categories and their order never move.

## Adding a link

Edit the `<script type="application/json" id="config">` block in `index.html`:

```json
{ "id": "finax", "label": "Finax", "sub": "robo-advisor",
  "url": "https://www.finax.eu/sk", "color": "cyan" }
```

`color` is one of `green`, `blue`, `amber`, `red`, `purple`, `cyan`. The `id`
also selects the card icon from the `ICONS` map further down the file — add a
matching entry there or the card falls back to a generic one. A category may
carry a `keywords` string, which is folded into the searchable text of every
card beneath it so a section stays findable under names other than its label.

A link with `"check": true` gets a status dot that probes whether the host is
reachable, for local services worth seeing the state of at a glance.

## Deployment

GitHub Pages serves the repository root, so pushing to `main` publishes it.
Pages does not always queue a build on push; force one with:

```
gh api -X POST repos/<owner>/homepage/pages/builds
```

A push landing is not evidence the site rebuilt — check the build actually
succeeded, since a failed one leaves the previous version live and the only
visible symptom is that nothing changed:

```
gh api repos/<owner>/homepage/pages/builds --jq '.[0] | "\(.status) \(.commit[0:7])"'
```

`.nojekyll` disables Jekyll. These are static files that need no preprocessing,
and running it only adds a build step that can fail on the content of the
markdown files.

### Why there is a service worker

GitHub Pages pins `Cache-Control: max-age=600` and offers no way to set
response headers. Past those ten minutes the browser must revalidate, which
costs a cold DNS, TCP and TLS handshake before a byte of HTML is parsed — on
the order of seconds. For a page opened by reflex on every new tab, that is the
dominant cost, and it is paid before any document exists, so no amount of
tuning inside the page can recover it.

`sw.js` removes the network from that path rather than making it faster. Once
installed it answers the navigation out of the Cache API with no request at
all, then refetches in the background to update the cache. The trade is that a
deploy shows up on the *next* new tab rather than the current one.

Consequences worth knowing:

- The first visit in a given browser profile still goes to the network; the
  worker takes over from the navigation after that.
- `shift`-reload bypasses the worker entirely. Once a worker is in play,
  "I reloaded and nothing changed" is not evidence of anything. **Testing one
  new tab per deploy means always looking at the previous build** — the `?`
  modal prints the served copy's `Last-Modified` so which build is on screen is
  never a guess.
- Removing `sw.js` from the repository does **not** uninstall it. A registered
  worker lives in the browser profile and keeps serving its cache. To retire it,
  either unregister per machine via `about:debugging#/runtime/this-firefox`, or
  deploy a tombstone in place of the worker:

  ```js
  self.addEventListener('install', () => self.skipWaiting());
  self.addEventListener('activate', e => e.waitUntil(
    self.registration.unregister().then(() => caches.delete('homepage-v1'))
  ));
  ```

## Local development

```
python3 serve.py        # http://localhost:8777/
```

Serves the working tree with `Cache-Control: no-store`, so a save shows up on
the next load with no push and none of the worker's one-tab lag. Use this while
editing rather than the deployed copy.

It binds both `127.0.0.1` and `::1`. `localhost` resolves to both, and a
browser that picks the IPv6 address gets a refusal from an IPv4-only listener
even though `curl` succeeds by falling back. Neither address is reachable from
the network.

## Browser new tab

Any extension that overrides the new tab page and accepts a URL will do;
Firefox refuses `file://` for this, so the page has to be served. Point it at
the deployed URL **with the trailing slash** — without it you pay a 301 on
every single tab.
