---
name: builder
description: Build and upgrade OpenClaw agents with deterministic lifecycle, Doppler secrets, and GitHub release flow
metadata: {"openclaw":{"always":true,"emoji":"🏗️","agents":["builder"]}}
---

# Builder Skill

## When to Activate

- Create a new OpenClaw-compatible agent from a structured spec
- Upgrade an existing agent structure or dependencies
- Validate runtime backend authentication and Doppler readiness
- Install external skills from SkillsMP API on demand

## Workflow

1. Validate runtime:

```bash
python /home/builder/scripts/run_builder.py --action validate-runtime
```

2. Generate a new agent:

```bash
python /home/builder/scripts/run_builder.py --action generate --spec /path/to/spec.yaml
```

3. Upgrade an existing generated agent:

```bash
python /home/builder/scripts/run_builder.py --action upgrade --spec /path/to/upgrade-spec.yaml
```

4. Install SkillsMP skill lazily:

```bash
python /home/builder/scripts/run_builder.py --action install-skill --skill-id <skill-id>
```

## Rules

- Keep execution sequential and deterministic
- Never bypass Doppler for secret inputs
- Block release if baseline validation fails
- Release means commit + semver tag + push
