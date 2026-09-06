import { total } from "./pricing.js";

export function createCart() {
  return { lines: [] };
}

export function addLine(cart, sku, quantity) {
  cart.lines.push({ sku, quantity });
  return cart;
}

export function lineCount(cart) {
  return cart.lines.length;
}

export function cartTotal(cart) {
  return total(cart.lines);
}
