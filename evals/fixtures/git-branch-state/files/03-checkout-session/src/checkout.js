import { total } from "./pricing.js";

export function startSession(cart) {
  return { id: "session", amount: total(cart.lines), state: "open" };
}

export function confirm(session) {
  return { ...session, state: "confirmed" };
}
