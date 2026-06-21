# Golden-State Report

The final output of a `setup-engineer` run. Keep it tight and scannable. It tells the repo owner
what state the repo is in, what you changed, and what (if anything) is left.

```
# Golden-State Report — <repo> (instance index <N>)

Classification: greenfield | partial | golden

## Drift found
<the diff table from step 3, or "none — repo was already golden">

## Changes applied (by phase)
1. <phase name> — <what changed>            verified: just doctor ✓  just test ✓
2. <phase name> — <what changed>            verified: just doctor ✓  just test ✓
...

## Final state
just doctor: ✓ all invariants pass
just test:   ✓ <suite summary>

## Left for follow-up
- <anything deferred, with why>            (or "nothing")
```

Rules:

- **Never report green you didn't verify.** Every phase line must name the command that proved
  it. If `just test` was skipped or partial, say so explicitly — don't imply a clean pass.
- If `doctor` still fails at the end, the run is **not** done. Report the failing checks and the
  plan to close them rather than declaring success.
- Mention the lifecycle-hygiene reflex if you left an environment running: either `just down` it
  as the last action, or tell the owner it's still up and why.
