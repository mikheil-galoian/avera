# Task: design-task-name

## Type

design

## Goal

Describe the UI/UX outcome.

## Allowed Zones

- `app/app/...`
- `app/src/components/...`
- `app/assets/...` when needed
- `docs/...` when needed

## Forbidden Zones

- backend logic
- database schema
- auth behavior
- financial calculations

## States To Check

- default
- loading
- empty
- error
- long text

## Verification

- run app or relevant preview
- inspect affected screen/flow

## Stop If

- design needs new backend data
- design requires navigation or API contract changes
