# Catchup: feature/checkout-flow

You are on **feature/checkout-flow**, 2 commits ahead of **main**, with one
uncommitted edit outstanding.

## Commits since main

1. `f8bea67` Add the checkout session module
2. `5e5490c` Wire pricing into the cart

## Files changed against main

- `src/checkout.js` — added: opens a checkout session against the cart total.
- `src/cart.js` — modified: gained `cartTotal()`.
- `src/pricing.js` — modified: `taxOnly()` was added.
- `src/refunds.js` — added: refund handling for confirmed sessions.

## Uncommitted

- `docs/notes.md` — modified but not committed.

## Where this leaves you

The branch is a clean, self-contained addition of checkout and refund handling
on top of the existing pricing code. Nothing was removed.
