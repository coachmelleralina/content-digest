# ADR 005 — GitHub Flow + CI + branch protection (safe multi-agent workflow)

## Status

Accepted.

## Context

Until now, agents worked on local feature branches (often in git worktrees), and the
orchestrator merged them into `main` **locally** and pushed `main` directly. This was fast and
had good per-agent isolation, but it had no gate: anything reaching `main` deploys to prod
(Vercel) immediately, with no automated check and no visible review surface. With multiple
agents working in parallel, the owner wanted the safer, more transparent flow used in typical
GitHub projects — visible branches, Pull Requests, and automated checks before merge.

## Decision

Adopt **GitHub Flow** with automated CI and branch protection:

1. **One branch per task/agent**, pushed to GitHub (not merged locally).
2. **A Pull Request** opens the branch against `main`. The PR is the review/merge surface.
3. **CI runs on every PR** (`.github/workflows/ci.yml`): two required status checks —
   `frontend` (npm lint + vitest + build) and `backend` (pytest). A red check blocks merge.
4. **`main` is protected** (configured via the GitHub API):
   - a Pull Request is required (no direct pushes to `main`),
   - the `frontend` and `backend` checks must pass and the branch must be up to date,
   - 0 required human approvals — an agent may merge its own PR **once CI is green**
     (the owner's chosen mode; she can still review/merge manually anytime),
   - `enforce_admins = false` — the owner keeps an emergency override.
5. **Merge style:** squash, then delete the branch.

This supersedes the local-merge habit from the prior waves. The boilerplate's "Deferred" list
already anticipated GitHub Actions and branch protection as the maturation step — this is it.

## Consequences

- `main` stays deployable: nothing lands without green tests, lint, and a successful build.
- Every change is visible as a branch + PR with a diff and check results before it merges.
- Agents follow: `branch → push → open PR → wait for green CI → squash-merge → delete branch`.
  The CLAUDE.md working agreement is updated to make this the default.
- Slightly slower per change (CI takes ~1–2 min) in exchange for a real safety gate.
- Vercel preview deployments per PR (Level 4) are **not** part of this ADR — they need the
  GitHub↔Vercel connection (which failed during `vercel link`); revisit separately. Prod still
  deploys via `npx vercel deploy --prod` from `main` until that connection exists.

## Emergency override

Because `enforce_admins = false`, the repo owner can, in a genuine emergency, push to `main`
directly or merge without a green check. This is intentional (avoids lockout) and should be
rare.
