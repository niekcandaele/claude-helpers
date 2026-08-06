# The Env / Port Contract

This is the failure-prone core. The whole design exists to make the *wrong* thing impossible:
you cannot add a service and forget the offset, and you cannot wipe an instance and leave data
behind, because the slot table and `nuke` are the single sources of truth and `doctor` checks
them.

Both reference repos (akari, takaro) independently converged on this shape. The canonical form
below is the cleaned-up version they should both be migrated toward.

## The two input variables

Everything else is derived from these two.

| Var | Default | Meaning |
|---|---|---|
| `<PROJECT>_ENV_INDEX` | `0` | Sole multi-instance identity. Instance 0, 1, 2, … `COMPOSE_PROJECT_NAME` derives from it so instances never share containers or volumes. |
| `<PROJECT>_DEV_HOST` | `127.0.0.1` | The host the browser/devbox reaches the stack at. Set to a devbox name (e.g. `devbox`) and *every* host-crossing URL switches to it automatically. |

## The port formula

```
host_port = BASE + INDEX*100 + slot
```

- **`BASE`** — a per-repo constant (akari 25000, takaro 13000). Pick a band unlikely to collide
  with other repos you run.
- **Stride is 100, with a hard slot ceiling of 100.** `doctor` fails any slot ≥ 100 and any two
  slots that collide. 100 ports per instance is plenty; a wider stride just wastes the port
  space and makes bands harder to reason about.
- **The slot table lives inside the CLI** and is the single source of truth. Adding a service is
  *one* new slot entry. Nothing else assigns a host port.

Example slot table (illustrative):

```
slot  0   API
slot  1   API debug/inspector
slot  2   Postgres
slot  3   Redis
slot  7   Keycloak / IdP
slot 80   public reverse-proxy (marketing)
slot 81   public reverse-proxy (app)
```

`doctor` parses the compose file(s) and asserts every published host port equals
`BASE + INDEX*100 + slot` for a slot that exists in the table — no literal host ports anywhere
else.

## The boundary law (the subtle, most-violated rule)

> Traffic **inside** Docker always uses container DNS + the service's fixed internal port and is
> **never** offset. Only URLs that **cross the host boundary** use `HOST:offset-port`.

So:

- Container-to-container config uses `postgresql:5432`, `redis:6379`, `keycloak:8080` — fixed,
  unoffset, because Docker's internal network doesn't see the host port mapping.
- Anything a browser, a devbox, a host-run tool, or an external token validator touches uses
  `HOST:offset-port`.

The CLI **derives** every host-crossing URL from `HOST` + the relevant slot's port, and writes
them into `.env`. These are never hand-typed and never committed into realm JSON:

- auth issuer (`http://HOST:idp_port/realms/<realm>`)
- OIDC redirect + post-logout URIs
- CORS allowed origins (include both the `HOST` form and the `127.0.0.1` form when they differ,
  plus the in-network container origins)
- frontend API URL (e.g. `VITE_API`)
- public base URL / marketing URL

When an auth server needs its public identity (Keycloak `KC_HOSTNAME`, issuer), that comes from
the same derived host-crossing URL, so tokens validate regardless of whether you reach the stack
as `127.0.0.1` or `devbox`.

## Generated .env, secrets preserved

`.env` is *rendered*, not authored:

- The CLI rewrites only **managed** keys: ports, `COMPOSE_PROJECT_NAME`, and all derived
  host-crossing URLs.
- It **preserves** secrets and developer-owned values (passwords, API keys, a hand-set
  `DEV_HOST`).
- Regeneration runs automatically on `up`, and running it twice is a no-op (`doctor` checks
  this).

## Headless devbox + HTTPS: derived, not a checklist

The localhost-vs-remote quirks become a single switch keyed off `DEV_HOST`. When
`DEV_HOST != 127.0.0.1`, the CLI automatically:

- adds the devbox host to the frontend dev server's allow-list (Vite `server.allowedHosts`);
- relaxes the IdP's SSL-required / hostname-strict settings so plain HTTP works over the LAN
  (e.g. Keycloak `SSL_REQUIRED=none`, `KC_HOSTNAME_STRICT=false`);
- adds the `extra_hosts` gateway mappings so containers can reach the public hostname.

The dev stack is plain HTTP on loopback/LAN — no self-signed certs. The headless-box pain you
used to hit by hand is now a consequence of one variable, enforced consistently.

## Why this kills the motivating bug

A new datastore added to compose without the offset would: publish a literal host port (fails
the slot-table check), likely lack a healthcheck (fails `up`'s readiness gate), and not be in
`nuke`'s volume list (fails the nuke-coverage check). Three independent `doctor` checks catch it
before it can rot the local environment. That's the infra-change law made mechanical.
