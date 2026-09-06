// A Promptfoo custom provider that stands in for a harness.
//
// It exists so every routine check — grader calibration, the execution-error
// path, the ungraded path — runs with no model credentials, no network and no
// subscription allowance. Behaviour comes entirely from `config`.
//
//   mode: respond  -> returns the contents of config.responseFile
//   mode: error    -> returns a provider error (an execution error, not a
//                     failed assertion)
//   mode: empty    -> returns an empty response (nothing to grade)

import { readFileSync } from "node:fs";

export default class DoubleProvider {
  constructor(options) {
    this.config = options?.config ?? {};
    this.label = options?.label;
    this.providerId = options?.id;
  }

  id() {
    return this.config.id ?? this.providerId ?? "double";
  }

  async callApi(prompt, _context) {
    const mode = this.config.mode ?? "respond";

    if (mode === "error") {
      return { error: `simulated execution error: ${this.config.message ?? "harness failed"}` };
    }

    if (mode === "empty") {
      return { output: "", tokenUsage: { total: 0, prompt: 0, completion: 0 } };
    }

    if (mode !== "respond") {
      return { error: `simulated execution error: unknown double mode "${mode}"` };
    }

    const output = readFileSync(this.config.responseFile, "utf8");
    return {
      output,
      tokenUsage: {
        total: prompt.length + output.length,
        prompt: prompt.length,
        completion: output.length,
      },
      metadata: { skillCalls: this.config.skillCalls ?? [] },
    };
  }
}
