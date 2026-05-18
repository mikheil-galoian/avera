# AVERA Runtime Stabilization

**Date:** 30 April 2026  
**Status:** Active runtime guidance  
**Purpose:** Define the supported local runtime path for AVERA core work and demo work

## Why This Exists

AVERA now has a strong local kernel and a green full test suite.

That shifts risk away from core logic and toward runtime ergonomics:

- which Python path is the safest
- how the demo shell should be launched
- how to detect when the shell path is shaky
- what fallback path still preserves showing continuity

This document defines that runtime contract.

## Supported Runtime Path

For the current AVERA stage, the recommended runtime path is:

1. use the repository `.venv`
2. run the launcher from the project root
3. use `scripts/runtime_doctor.py` before a live demo or shell-heavy session

Recommended commands:

```bash
.venv/bin/python scripts/runtime_doctor.py
./start_demo.sh
```

## Current Runtime Reality

### Core And Test Work

The current project runtime is acceptable for:

- CLI analysis
- fixture matrix runs
- contract validation
- `pytest`
- report generation
- decision/traceability/trend/pack flows

### Demo Shell Work

The demo shell is usable, but it has one known runtime quirk:

- `Python 3.14 + Streamlit` may cold-start slowly

That should be treated as a demo/runtime issue, not as evidence that the AVERA
kernel is unstable.

## Runtime Doctor

Use:

```bash
.venv/bin/python scripts/runtime_doctor.py
```

It reports:

- Python executable
- Python version
- whether the project `.venv` is active
- whether `streamlit` is available
- whether the ADAS static showcase is present
- whether the protobuf runtime override is enabled

## Launcher Behavior

`./start_demo.sh` now does four important things:

1. prefers the repository `.venv`
2. warns when the selected runtime is `Python 3.14`
3. enables a safer protobuf fallback for the shell when appropriate
4. avoids trying to install demo dependencies into arbitrary external runtimes

If `streamlit` is missing in the selected runtime, the launcher now points the
operator to:

- the project `.venv`
- `scripts/runtime_doctor.py`
- the static ADAS showcase fallback

## Presentation Fallback

If the live Streamlit shell is slow to cold-start during a meeting, AVERA still
has a presentation-safe second-domain path:

- [AVERA_ADAS_SHOWCASE.html](/Users/mac/Desktop/AVERA/docs/AVERA_ADAS_SHOWCASE.html)

This is not the primary demo route.

It is the continuity route that keeps the meeting moving without pretending that
the runtime quirk is part of the product truth.

## What This Stabilization Layer Solves

This layer gives AVERA:

- one supported local shell path
- one diagnostic command
- one known runtime warning
- one safe visual fallback

That is enough to move from runtime guesswork to a controlled local operating
model.

## What Still Comes After This

Once this layer is accepted, the next product-hardening step should be:

- shell hardening

After that:

- realistic artifact adapters
- wider domain matrix
- pilot workflow preparation
