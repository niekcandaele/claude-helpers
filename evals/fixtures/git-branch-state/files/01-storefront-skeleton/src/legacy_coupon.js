const COUPONS = { WELCOME: 500, SUMMER: 250 };

export function redeem(code) {
  return COUPONS[code] ?? 0;
}
