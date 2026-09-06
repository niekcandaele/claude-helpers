const TAX_RATE = 0.21;

export function subtotal(lines) {
  return lines.reduce((sum, line) => sum + line.quantity * 100, 0);
}

export function total(lines) {
  return Math.round(subtotal(lines) * (1 + TAX_RATE));
}
