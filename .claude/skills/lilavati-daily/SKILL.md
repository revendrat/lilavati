---
name: lilavati-daily
description: Run Project Līlāvatī's one-goal-per-day cycle (open, review open pull requests, pick, goal card, build, prove, close). Use when the maintainer says /lilavati-daily, "start the day", "today's goal", "what next", or "close the day", asks to review or merge contributors' pull requests, or asks to plan or finish a day's work on the repository.
---

# One goal per day (maintainer workflow)

One achievable goal, completed cleanly, then the day is closed. The coding, testing and documentation
rules are in the `lilavati-dev` skill (load it before any change); this skill is the routine around
them.

## 1. Open (about five minutes)

Check, in this order, and report anything that changes the plan in one or two lines:

1. `git status`, open branches and pull requests (`gh pr list`), CI on `main`
   (`gh run list --branch main --limit 1`). An unmerged branch from an earlier day is finished first.
   Pull requests from anyone else are reviewed next (section 1b), before the goal is picked.
2. Deadlines in memory (for example the 1 December check of issues #15 and #16) and `*Due:*` items.
3. New reviewer comments or issues (`gh issue list`, `gh pr list --search "review"`), if the maintainer
   has mentioned any.
4. The handoff note in memory (`lilavati-next-work`): what was done, what carries over.

## 1b. Review open pull requests (before the goal)

Every open pull request from someone else (an outside contributor, a dependency bot) is reviewed each day
before the goal is picked, and merged that day when it passes; a contributor should not wait on the
maintainers' own work. Oldest first, for each one:

1. Read the linked issue's "Done when" and the whole diff (`gh pr view <n>`, `gh pr diff <n>`).
   Re-verify every claim in the description yourself; a contributor's report is not evidence.
2. Check it out in a scratch worktree, not in the main checkout:
   `git fetch origin pull/<n>/head:pr-<n>`, `git worktree add <scratchpad>/pr<n> pr-<n>`, then
   `uv sync --extra dev` there (a new worktree's environment has no dev tools, so every check "fails").
   Confirm the PR's copy is the one imported (`module.__file__`).
3. For a fix: run the new tests against the code on `main` (they must fail) and against the PR (they must
   pass). Copy `main`'s version of the changed file in, run, then restore it and check `git status` is clean.
4. Run `scripts/check_all.py --fast` on the PR code, and every example, tutorial and agent that reaches the
   changed code (grep for callers): a new input check can make a caller with real data raise. CI on the PR
   must be green.
5. Review against `lilavati-dev`: references cited next to expected values, tests that can fail (not
   vacuous assertions), no invented numbers, section 4b done (docstring, validation page, status,
   CHANGELOG), no claims-linter workarounds, and no other page still describing the old behaviour.
6. Post the review (`gh pr review <n> --approve` or `--request-changes`, `--body-file`): thank the author,
   then list what you checked with the results, then the findings, numbered and marked blocking or
   optional. Any value you quote (an expected result, a hand calculation) must come from code you ran.
7. Merge when nothing is blocking and CI is green: `gh pr merge <n> --merge` (`--delete-branch` only for a
   branch in this repository, not a fork). An optional finding does not hold a merge; if you will do it
   yourselves, add it to TODO.md or an issue. With a blocking finding, request changes and do not merge.
8. After merging: pull `main`, check that the linked issue closed and CI on `main` passed, and remove the
   worktree and the `pr-<n>` branch.

**Approval (chosen 2026-11-27):** the maintainer made reviewing and merging pull requests part of the daily
routine, so posting a review and merging a pull request that passes needs no further "go". Stop and ask
instead of merging when a pull request adds or upgrades a dependency; changes CI, release or docs
workflows, packaging (`pyproject.toml`), licence or security files, or GitHub settings; edits or deletes
evidence under `results/` or published benchmark cases; touches secrets handling; or goes beyond its
issue's scope. Report every review in the day's opening note: the pull request, the verdict and the
measured results.

## 2. Pick one goal

Run `uv run python scripts/next_goal.py`. It lists the unblocked TODO items, ranked: due items first,
then correctness (a bug, or a check that holds by construction), then validation (audits, reference
checks), then phase order. Blocked items (`*Blocked: <reason>.*`: maintainer action, reviewer feedback,
API budget, a key or secret, a file downloaded by hand) are not offered.

A goal is achievable in a day when it is unblocked, touches one engine or module, has an independent
reference or a clear acceptance test, and fits one pull request. An item flagged "split" is several days:
take one slice and record the slice in TODO.md. Prefer the top candidate unless a deadline or a broken
`main` says otherwise; say why if you pick another.

## 3. The goal card (wait for "go")

Send one card and wait:

```text
Goal (date): <one line>
Why: <the TODO/ROADMAP item, and why today>
Done means: <the reference or acceptance test; tests; docs, tutorial step, paper section if a milestone;
            all checks and CI green; merged>
Files: <expected>
Out of scope: <what this goal will not do>
Needs from you: <nothing | a download | a decision>
```

**Approval (model A, chosen 2026-11-26):** the maintainer's "go" on the card approves the commit, push,
pull request and merge for that goal, once every check and CI pass. Stop and ask instead of proceeding
for anything outside the card: a new dependency, GitHub settings, a paid API or key, anything
irreversible, or work beyond the card's scope.

## 4. Build

- Branch `day/<YYYY-MM-DD>-<slug>` from an up-to-date `main`.
- Follow `lilavati-dev`: read the code and tests first; for a bug, a failing test first; numeric code
  against independent references; no number in docs that you did not produce or read.
- Scope is frozen: anything new you find goes into TODO.md (marked blocked if it is), not into today.

## 5. Prove

- `uv run python scripts/check_all.py --fast` while working; the full `scripts/check_all.py` before the
  pull request. "No errors" means every check passes, CI passes, and every new number traces to a script,
  test or source read.
- Docs per `lilavati-dev` section 4b; papers per section 4c when the goal completes a milestone (the
  `papers` line of `check_all.py` shows whether a paper is behind).

## 6. Close

1. Commit (Conventional Commits, one logical change each), push, open the pull request, wait for CI with
   `gh pr checks <n> --watch`, merge (`gh pr merge <n> --merge --delete-branch`).
2. TODO.md: tick the item or the slice with the date; ROADMAP.md if a numbered item moved; CHANGELOG entry.
3. Memory: update `lilavati-next-work` (done today, next candidate, carry-overs) and any deadline.
4. Tell the maintainer in five lines: the goal, the result (with the measured numbers), the PR, the
   contributors' pull requests reviewed and merged, what is next, anything needed from them.

**If the goal is not finished:** do not merge half of it. Push the branch, record in TODO.md and in memory
where it stopped and why, and say so; finishing it is the next day's goal. If a check fails for a reason
outside the goal (a flaky provider, a broken dependency), report it with the output instead of working
around it.

## Why these rules

The project's credibility rests on every number being right. Most bugs found so far were in code that
looked finished: a check that could not fail, a stale figure in a paper, a script that crashed on a new
file type. One finished, checked goal a day keeps `main` releasable and the TODO honest. Contributors'
pull requests get the same checks as the maintainers' own, and are not left waiting behind the day's goal.
