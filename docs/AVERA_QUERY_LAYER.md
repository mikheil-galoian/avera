# AVERA Query Layer

**Date:** 28 April 2026  
**Status:** Draft core contract v0.1

## Purpose

The AVERA query layer is the local navigation surface over core artifacts.

It lets the engine answer focused questions about components, requirements,
tests, risks, and gate history without introducing a UI shell.

Core role:

`traceability index -> precise local lookup`

## Scope

The query layer is still part of the kernel.

It does not render dashboards, pages, or workflow screens. It provides stable,
machine-readable lookup behavior that a future UI can consume.

## Query Targets

Current query kinds:

- `component`
- `requirement`
- `test`
- `risk`
- `gate`

## Inputs

The layer reads the traceability index as its primary source:

- `avera-traceability-index.json`

It may later grow to read workspace packs directly, but the first contract stays
small and deterministic.

## Output Shape

The query should return:

- one matched record
- or no match

The CLI should print:

- traceability source path
- query kind
- query value
- matched JSON record or `none`

## CLI

```bash
PYTHONPATH=src python3 -B -m avera query \
  --traceability reports/avera-traceability-index.json \
  --kind component \
  --value "BMS Thermal Control"
```

## Why This Is Core

The query layer matters before UI because it gives the engine a stable internal
navigation contract:

- decision logic can retrieve focused evidence
- export layers can validate references
- future agents can ask structured questions
- future UI can stay thin over a proven kernel API

## Future Development

- multi-match queries
- filtering by recency or verdict
- pack-level queries
- query summaries
- query validation and error taxonomy
