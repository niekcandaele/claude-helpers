const TAX_RATE = 0.21;
const UNIT_PRICE = 100;

export function subtotal(lines) {
  return lines.reduce((sum, line) => sum + line.quantity * UNIT_PRICE, 0);
}

export function total(lines) {
  return Math.round(subtotal(lines) * (1 + TAX_RATE));
}

export function taxOnly(lines) {
  return total(lines) - subtotal(lines);
}
