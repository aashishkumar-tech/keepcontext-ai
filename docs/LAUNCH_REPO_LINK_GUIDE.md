# Launch Guide: Why The Repo Link Must Be In README

When launching a product, attention comes from posts, demos, and announcements.
Adoption happens only when users can quickly find the official repository.

## Why This Matters

1. Trust and credibility

- Users can verify source code, commit history, and release quality.

1. Single source of truth

- Setup, docs, issues, and releases all live in one place.

1. Faster onboarding

- Users can clone, run, and validate in minutes.

1. Better support

- Bug reports and feature requests become trackable via issues.

1. Long-term maintainability

- Future contributors and team members can recover context from one canonical home.

## What To Add In README For Launch

Add these sections near the top of root README:

1. Official repository link
2. Live/demo link (if available)
3. Quick start in 60 seconds
4. Health check endpoint
5. Support and issue reporting path

## Recommended Top-Of-README Block

```markdown
## Official Links

- Repository: https://github.com/<org-or-user>/<repo>
- Documentation: https://github.com/<org-or-user>/<repo>/tree/main/docs
- Issues: https://github.com/<org-or-user>/<repo>/issues
- Releases: https://github.com/<org-or-user>/<repo>/releases
```

## Launch-Day Validation Checklist

1. README has the official repository URL.
2. README quick start is tested on a clean machine.
3. README links to docs index and troubleshooting.
4. README includes health endpoint and expected success response.
5. README points to issue tracker and contribution guide.
6. License is present at repo root.

## Common Mistakes To Avoid

1. Multiple conflicting repo links across docs.
2. Example commands with different default ports.
3. Missing issue/support links.
4. No clear first-success verification step.
5. Announcing product without public setup instructions.

## KeepContext AI Example

- Repository: <https://github.com/aashishkumar-tech/keepcontext-ai>
- Root README: ../README.md
- Docs index: ./README.md
