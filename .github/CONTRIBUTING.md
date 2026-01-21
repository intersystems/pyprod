# Contributing to pyprod

Thank you for your interest in contributing to **pyprod** 🎉  
pyprod is an open-source project that enables developers to write **InterSystems IRIS Interoperability Productions using purely Python**, while preserving the original Production architecture and behavior.

This document explains the **goals, constraints, and expectations** for contributors.

---
## Process

PyProd's primary maintainers are a highly invested team within InterSystems. We welcome community contributions, but at times may have limited bandwidth for thorough reviews.

### Bug fix - regression

InterSystems will create, review and merge PRs urgently (target: <1 week).

### Bug fix - non-regression

InterSystems will create, review and merge without a milestone associated with the issue (target: within 1 month).

### Enhancements 

We need to ensure alignment with the overall roadmap and existing design. To avoid wasting your time, obtain the maintainer's signoff on a spec _before_ doing extensive implementation work. This is *required* before PR review.
* If a feature issue is assigned to an InterSystems employee, that means that work may be in progress. Contributors should verify with the assignee before beginning work.
* Report a GitHub issue to discuss and hone the spec. The final spec will go into the issue. While pending specification, the issue will be given the "needs spec" label and should not be actioned.
    * Features we would like to see or implement in a certain timeframe will have an associated milestone.
    * Features where we would particularly welcome community contribution will have the "help wanted" label.

## Submitting changes

1. Fork the repository
2. Create a focused feature or fix branch
3. Make your changes following the principles below
4. Submit a pull request with:
   - A link to the relevant GitHub issue
   - A clear description of **what** changed
   - A justification for **why** it aligns with pyprod’s philosophy

## What we look for in contributions

Good contributions typically:
- Reduce friction for Python developers using IRIS Productions
- Expose existing Production capabilities more clearly in Python
- Improve correctness, clarity, or maintainability
- Reduce boilerplate without changing semantics

## What we will likely reject

We will likely reject contributions that:
- Add third-party Python dependencies
- Redesign or abstract away the Production architecture
- Introduce Python-only concepts that don’t map to Productions
- Attempt to “improve” Productions rather than expose them
- Mimic ObjectScript patterns instead of using Python idioms

## Development guidelines

- Keep changes minimal and well-scoped
- Favor clarity over cleverness
- Add comments where IRIS concepts may not be obvious to Python developers
- Avoid speculative or future-facing abstractions

## Project philosophy

pyprod is intentionally opinionated. Any contribution must align with **all** of the principles below.

### 1. Python-first authoring of IRIS Productions
- pyprod allows users to **define and implement IRIS Interoperability Productions in Python**.
- Users should not be required to write ObjectScript as part of normal development.
- The result must still be a real IRIS Production with standard components and behavior.

### 2. Zero third-party Python dependencies
- pyprod has **no third-party Python dependencies**, and we do not want them.
- Contributions **must use only the Python standard library**.
- Do not introduce dependencies for convenience, performance, or syntactic sugar.

### 3. Accessibility, not reinvention
- The goal is **not** to make IRIS Productions “better” or “more modern.”
- The goal is to make them **accessible to developers who primarily or only know Python**.
- IRIS Productions are treated as a proven system, not something to redesign.

### 4. Minimal new code
- Prefer **small, focused changes**.
- Avoid introducing new abstractions unless absolutely necessary.
- If something already exists in IRIS, prefer exposing it rather than recreating it.

### 5. No external binding libraries
- Do **not** introduce external libraries for Python ↔ ObjectScript binding.
- The only acceptable runtime dependency is the **IRIS-provided `iris` Python module**.
- Setup should be limited to adjusting the Python path to point to an IRIS installation.

### 6. Treat Productions as the underlying “library”
- ObjectScript Productions are treated as the **core system/library**.
- Python code interfaces with that system rather than replacing or emulating it.
- Where needed, pyprod exposes Production concepts to Python users.

### 7. Preserve Production architecture
- The **core Production architecture must remain unchanged**.
- The fundamental way Productions are designed, wired, and executed must stay the same.
- Python should not introduce an alternative or simplified mental model.
- Any architectural change must make sense **for both Python and ObjectScript**, not just Python.

### 8. Pythonic API design
Python-facing APIs must feel natural to Python developers:

- No `ByRef` or output parameters
- Prefer return values and exceptions
- Objects should be constructed using normal Python initialization
- Favor clear, idiomatic Python over mirroring ObjectScript syntax

### 9. Compatibility with modern Python tooling
pyprod should work well with standard Python tooling, including:

- Linters and formatters
- Debuggers
- IDEs and editors

Contributions should not break or bypass these workflows.

## Final note

pyprod exists to **bridge skill sets, not rewrite systems**.  
When in doubt, ask:

> “Does this make IRIS Productions more accessible to Python developers *without changing what a Production fundamentally is*?”

If the answer is yes, it’s probably a good contribution.

