---
doc_id: md-frontmatter-01
status: review
version: 2.1
owner_primary: ops
owner_backup: finance
release_window: 2024-11-30
---

# Nested Lists + Inline HTML

- region: NA
  - tasks_complete: 5
  - blockers: 0
- region: EU
  - tasks_complete: 3
  - blockers: 1
- region: APAC
  - tasks_complete: 4
  - blockers: 0

<div class="inline-insight">
  <p data-field="hint">capacity: yellow</p>
  <table>
    <tr><th>metric</th><th>value</th></tr>
    <tr><td>throughput</td><td>120</td></tr>
    <tr><td>latency_ms</td><td>85</td></tr>
  </table>
</div>

Inline JSON example below keeps the parser busy:
{
  "region": "LATAM",
  "tasks_complete": 2,
  "tier": "md-frontmatter",
  "capacity_plan": {
    "owners": ["ops-latam", "partner-success"],
    "milestones": [
      {"name": "kickoff", "week": 45},
      {"name": "close-out", "week": 47}
    ]
  }
}

Additional KV pairs keep coverage dense.
insight_owner: platform
html_hint: inline
