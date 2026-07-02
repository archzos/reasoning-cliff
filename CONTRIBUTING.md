# Contributing to reasoning-cliff

Thanks for contributing. This project focuses on deterministic reasoning
measurement, so changes should prioritize methodological correctness and
reproducibility.

## Development setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
pytest
```

## Contribution workflow

1. Fork the repo and create a branch from `main`.
2. Keep pull requests scoped and focused.
3. Add or update tests for behavior changes.
4. Run `pytest` locally before opening the PR.
5. Open a PR with clear methodology impact notes.

## Pull request checklist

- [ ] Tests added/updated for new behavior
- [ ] Backward compatibility considered
- [ ] Methodology behavior documented (if changed)
- [ ] README/docs updated (if user-facing behavior changed)
- [ ] No secrets or credentials introduced

## Code style guidance

- Prefer explicit, deterministic logic over implicit heuristics.
- Keep verifier/scoring paths easy to audit.
- Minimize hidden assumptions in experiment orchestration.

## Reporting issues

- Use GitHub issues for bugs and feature requests.
- For vulnerabilities, do not open public issues. See `SECURITY.md`.

## Issue triage and labels

Use labels consistently for queueing and prioritization:

- `priority:p0`: ship-blocking or methodology-integrity defects
- `priority:p1`: important improvements needed for Day 1/Day 2 goals
- `priority:p2`: useful follow-up or governance polish
- `day-1`, `day-2`: delivery phase tracking
- `puzzle`, `metrics`, `runner`, `plots`, `docs`, `ci`: component ownership
- `extension`: explicitly out-of-scope for v1

Triage policy:

1. New bug/security-suspected issues: acknowledge within 72 hours.
2. Apply `priority:*` and component label at triage time.
3. If issue changes benchmark claims or failure typing, mark as `priority:p0`.
4. Close only with one of: merged fix, duplicate, invalid, or wontfix with rationale.
