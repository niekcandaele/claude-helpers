// Promptfoo `javascript` assertion for the git-branch-state fixture.
//
// Grades observable facts about the fixture's repository, one component per
// fact, so the viewer shows which fact was missed and what was looked for
// rather than a single opaque boolean. The facts come from the fixture
// manifest, which is also what build.sh builds from — grader and fixture
// cannot drift apart.

import { readFileSync } from "node:fs";

const normalize = (text) => text.toLowerCase().replace(/\s+/g, " ");

// Promptfoo flattens these sub-results into the same list as the case's own
// assertions, so the prefix is load-bearing: it is how the summariser tells a
// fact of this module apart from an assertion the case declared.
function component(pass, name, reason) {
  return {
    pass,
    score: pass ? 1 : 0,
    reason,
    assertion: { type: "javascript", metric: `git:${name}` },
  };
}

// A path counts as mentioned by its full path or by its bare file name; a
// summary that writes `checkout.js` has still named the file.
function mentionsPath(haystack, path) {
  const base = path.split("/").pop();
  return haystack.includes(normalize(path)) || haystack.includes(normalize(base));
}

// Creation and deletion have to be said, on the line that names the file: a
// summary that quietly drops the deleted file, or lists it as just another
// change, has misreported the branch. Modification is graded on mention alone —
// a good summary often says what changed inside the file instead of labelling
// it "modified", and that is better writing, not a worse answer.
const DISPOSITION_WORDS = {
  added: ["added", "add ", "new ", "created", "introduc"],
  deleted: ["deleted", "delete", "removed", "remove", "dropped", "gone"],
};

function lineFor(response, path) {
  const base = path.split("/").pop();
  return response
    .split("\n")
    .filter((line) => {
      const l = normalize(line);
      return l.includes(normalize(path)) || l.includes(normalize(base));
    })
    .join(" ");
}

export default function assertGitBranchState(output, context) {
  const manifestPath = context?.test?.vars?.fixtureManifest;
  if (!manifestPath) {
    throw new Error(
      "fixtureManifest var is not set; the generated config must pass the absolute path of the fixture manifest",
    );
  }
  const manifest = JSON.parse(readFileSync(manifestPath, "utf8"));
  const expected = manifest.expected;

  const response = typeof output === "string" ? output : JSON.stringify(output);
  const flat = normalize(response);

  const results = [];

  results.push(
    component(
      flat.includes(normalize(manifest.branch)),
      "names-current-branch",
      `current branch "${manifest.branch}" ${flat.includes(normalize(manifest.branch)) ? "is named" : "is never named"}`,
    ),
  );

  results.push(
    component(
      new RegExp(`\\b${manifest.base_branch}\\b`, "i").test(response),
      "names-base-branch",
      `base branch "${manifest.base_branch}" ${new RegExp(`\\b${manifest.base_branch}\\b`, "i").test(response) ? "is named" : "is never named"}`,
    ),
  );

  const countPattern = new RegExp(
    `(\\b${manifest.commits_ahead}\\b[^.\\n]{0,40}commit)|(commit[^.\\n]{0,40}\\b${manifest.commits_ahead}\\b)`,
    "i",
  );
  results.push(
    component(
      countPattern.test(response),
      "commit-count",
      countPattern.test(response)
        ? `reports ${manifest.commits_ahead} commits ahead`
        : `does not state that the branch is ${manifest.commits_ahead} commits ahead`,
    ),
  );

  for (const subject of expected.commit_subjects) {
    const seen = flat.includes(normalize(subject));
    results.push(
      component(
        seen,
        `commit-subject:${subject}`,
        seen ? `commit "${subject}" is listed` : `commit "${subject}" is missing`,
      ),
    );
  }

  for (const change of expected.changes) {
    const seen = mentionsPath(flat, change.path);
    if (!seen) {
      results.push(
        component(false, `change:${change.path}`, `${change.path} is never mentioned`),
      );
      continue;
    }
    const words = DISPOSITION_WORDS[change.disposition];
    if (!words) {
      results.push(component(true, `change:${change.path}`, `${change.path} is reported as changed`));
      continue;
    }
    const line = normalize(lineFor(response, change.path));
    const correct = words.some((word) => line.includes(word));
    results.push(
      component(
        correct,
        `change:${change.path}`,
        correct
          ? `${change.path} is reported as ${change.disposition}`
          : `${change.path} is mentioned but not reported as ${change.disposition}`,
      ),
    );
  }

  for (const path of expected.uncommitted_paths) {
    const seen = mentionsPath(flat, path);
    const line = normalize(lineFor(response, path));
    const flagged =
      seen &&
      (["uncommitted", "unstaged", "not committed", "working tree", "working directory"].some(
        (word) => flat.includes(word),
      ) ||
        ["uncommitted", "unstaged"].some((word) => line.includes(word)));
    results.push(
      component(
        flagged,
        `uncommitted:${path}`,
        flagged
          ? `${path} is reported as an uncommitted change`
          : seen
            ? `${path} is mentioned but never identified as uncommitted`
            : `the uncommitted change to ${path} is missing`,
      ),
    );
  }

  const failed = results.filter((r) => !r.pass);
  const score = results.filter((r) => r.pass).length / results.length;

  return {
    pass: failed.length === 0,
    score,
    reason:
      failed.length === 0
        ? `all ${results.length} observable git facts are reported correctly`
        : `${failed.length} of ${results.length} git facts wrong: ${failed.map((r) => r.reason).join("; ")}`,
    componentResults: results,
  };
}
