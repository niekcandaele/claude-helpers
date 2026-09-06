# Storefront

A very small shop. The cart adds up line items, pricing turns them into a
total, and the legacy coupon path is still hanging around from the old site.

## Layout

- `src/cart.js` — the shopping cart
- `src/pricing.js` — totals and tax
- `src/legacy_coupon.js` — the old coupon redemption path
- `docs/notes.md` — working notes

## Pricing rules

Every line item costs one unit. Tax is a flat 21% applied to the subtotal and
rounded to the nearest whole amount.
