# Contributing to ZW Protocol

## Development Principles
- Prefer **intent extraction** over strict schemas.
- Changes must remain **backward tolerant**: new terms/fields should not break old inputs.
- Provide **examples** demonstrating noise tolerance and vocab remapping.

## Workflow
1. Fork the repo
2. Create a feature branch: `git checkout -b feature/my-change`
3. Add tests/examples under `examples/`
4. Open a PR with a clear description of the intent you enabled

## Commit Message Template
```
feat(parser): support alias 'combine' -> op
fix(calc): handle empty list gracefully
docs(readme): add ZW origin story
```
