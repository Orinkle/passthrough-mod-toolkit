# Repository name — DECIDED

> **Decision (2026-10-08, v4-launch round): `passthrough-mod-toolkit`**
>
> Why: it is the only candidate that contains the exact three-word phrase an agent
> would search (`passthrough mod`) **plus** a functional qualifier (`toolkit`) that
> separates us from SEO content farms. All four candidates were verified unoccupied
> (`gh api search/repositories?q=<name>+in:name`, 2026-10-08). The CLI stays `ptgen`
> (short to type; repo name and CLI name are not required to match).
>
> Hedge in effect: the runners-up (`bridge`, `ipc`, `skeleton`, `scaffold`, `cross-game`)
> all live in the description / topics / README below, so the repo still matches those
> query lanes. The candidate analysis is kept at the bottom of this file for the record.

## Final metadata (copy-paste ready)

**GitHub About → Description** (154 chars):

```
A toolkit for passthrough mods: two games as two processes bridged over local IPC. Schema-driven protocol codegen, fake-host stubs, MCP server. No game files.
```

**GitHub About → Topics** (12):

```
passthrough-mod  game-modding  ipc  shared-memory  codegen  toolkit
minecraft  skse  bepinex  reverse-engineering  modding-tools  schema-driven
```

**Website:** leave empty until a docs page exists. **Releases/Packages:** off until tagged.

gh CLI equivalent (run from the local clone after `gh repo create`):

```bash
gh repo edit --description "A toolkit for passthrough mods: two games as two processes bridged over local IPC. Schema-driven protocol codegen, fake-host stubs, MCP server. No game files." \
  --add-topic passthrough-mod --add-topic game-modding --add-topic ipc \
  --add-topic shared-memory --add-topic codegen --add-topic toolkit \
  --add-topic minecraft --add-topic skse --add-topic bepinex \
  --add-topic reverse-engineering --add-topic modding-tools --add-topic schema-driven
```

---

# Below: the candidate analysis that led to the decision (archived)

## How to judge a candidate (2026-10-08: criterion changed)

The old criterion was "does a human like it". The criterion that matters now is:

> **When an agent is asked to find a tool for building a passthrough mod,
> which name does it match first?**

That means, in priority order:

1. **Contains the words an agent would put in a search query** — `passthrough`,
   `bridge`, `cross-game`, `game mod`, `codegen` / `scaffold` / `toolkit`.
   Agents match keywords literally; puns and invented words match nothing.
2. **Not colliding with an existing repo of the same name** — verify with
   `gh api "search/repositories?q=<name>+in:name"` before committing.
3. **Beats the SEO noise** on `passthrough` (many junk pages scrape mod
   descriptions) — a functional qualifier (`-toolkit`, `-scaffold`, `-codegen`)
   separates us from content farms.
4. Only then: how it sounds out loud.

> Note: the shipped CLI is **`ptgen`**. Repo name and CLI name are not required to
> match, and `ptgen` is short enough to type.

## Candidates considered

- **`ptmodmaker`** (old default) — weak on literal matching; dropped.
- **`twogames-bridge`** — clean to say, contains neither `passthrough` nor `mod`; dropped.
- **`passthrough-skeleton`** — good; matches `passthrough` but not the full
  `passthrough mod` phrase; runner-up.
- **`ipc-bridge-scaffold`** — owns the mechanism lane, but an agent asked about
  "passthrough mods" may not match `ipc`; dropped.
- **`passthrough-mod-toolkit`** ⭐ — **chosen.** Literal phrase + qualifier, uncontested.

## Availability check (verified 2026-10-08, `gh api search/repositories?q=<name>+in:name`)

| Candidate | Same-name repos found |
|---|---|
| `ptmodmaker` | none |
| `passthrough-skeleton` | none |
| `ipc-bridge-scaffold` | none |
| `passthrough-mod-toolkit` | none |
| `twogames-bridge` | none |

(The only near-hit anywhere was `vfio-full-passthrough-setup-toolkit-fedora`, an
unrelated GPU-passthrough script repo — different domain, no collision.)
