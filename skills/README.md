# partinfo skill

`partinfo/SKILL.md` teaches a coding agent to answer component questions with
the `partinfo` CLI instead of guessing pinouts from memory. It is a single
portable skill file (YAML frontmatter plus instructions) and works with any
agent that reads the `SKILL.md` format.

## Prerequisite

The skill only wraps the CLI, so install that first:

```sh
pip install partinfo        # once published
# or from a checkout:
pip install -e .
```

Confirm `partinfo ne555` prints an entry before installing the skill.

## Claude Code

Copy or symlink the skill into your skills directory:

```sh
mkdir -p ~/.claude/skills
ln -s "$PWD/partinfo" ~/.claude/skills/partinfo
```

Claude Code discovers it on the next session; it triggers on component
lookups (see the `description` in `SKILL.md`).

## Codex

Codex loads the same `SKILL.md` format. Copy or symlink the skill into its
skills directory:

```sh
mkdir -p ~/.codex/skills
ln -s "$PWD/partinfo" ~/.codex/skills/partinfo
```

There is deliberately one skill file for both agents rather than two copies to
keep in sync. If your Codex build scans a different path, point that path at
`skills/partinfo/` the same way.
