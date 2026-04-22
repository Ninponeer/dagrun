# DAGrun Markdown Rulesets

Rulesets let you convert *many different* Markdown styles into `.plan` files without changing code.

## Quick start

Extract actionable items (agent-friendly JSON):

```bash
python -m dagrun md extract "path/to/doc.md" > items.json
```

Convert Markdown to a `.plan` using a ruleset:

```bash
python -m dagrun init
python -m dagrun md to-plan "path/to/doc.md" --rules "rulesets/generic_checklists.v1.yaml"
python -m dagrun validate ".dagrun/doc.plan"
```

## Ruleset format (YAML)

All rulesets follow this schema:

```yaml
version: 1
rules:
  - name: deliverables
    prefix: D
    mode: either        # pull | push | either
    action: execute     # opaque token for agents
    agent: null         # optional, else CLI --agent

    # Matching (all are optional)
    match_section_contains: ["deliverable"]
    match_heading_path_contains: ["next priorities"]
    match_kind: ["checkbox", "numbered", "bullet"]

    # Exclusions (all are optional)
    exclude_section_contains: ["session notes"]
    exclude_heading_path_contains: ["partnership context"]
    exclude_kind: ["bullet"]
```

### Matching semantics

- **First match wins**: rules are evaluated in order. The first rule that matches an extracted item gets it.
- **Case-insensitive contains**: `match_*_contains` does substring matching against:
  - `section`: the nearest heading text
  - `heading_path`: any heading in the ancestry (H1..H6)
- **Kinds**:
  - `checkbox`: `- [ ]` / `- [x]`
  - `numbered`: `1.` / `1)`
  - `bullet`: `- item` / `* item`

## Design guidance

- **Prefer “high precision” rulesets for spec docs**: limit to sections like “Next Steps”, “Roadmap”, “TODO”, “Immediate”.
- **Prefer “high recall” rulesets for action plans**: include checklists and priority lists broadly.
- **Always include a final `fallback` rule** (e.g. prefix `T`) if you want to capture everything.

## Included rulesets

- `generic_checklists.v1.yaml`: checkboxes + numbered lists + limited bullets
- `tdd_oracle_session.v1.yaml`: tuned for `Volume_ZZ_the_Oracles` style action plans
- `tdd_master_roadmap.v1.yaml`: tuned for `00.01_I_master_roadmap.md`

