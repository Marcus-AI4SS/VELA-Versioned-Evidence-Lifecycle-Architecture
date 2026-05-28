# Output Schema

## Default Summary Table

`index | platform | title | author | time | 100-200 char summary | link`

## Per-item Evidence Block

Each item should be normalized as:

```text
item_index:
platform:
artifact_type:
title:
author:
published_at:
body_or_caption:
tags_or_topics:
media_type:
source_link:
evidence_boundary:
short_explanation:
```

## Comment Block

When visible comments are requested:

`comment rank | note title | author | like count | content | scope note`

## Artifact Notes

If `agent-browser` was used, append:

```text
artifact_dir:
snapshot_json:
screenshot_path:
state_file:
```

Use `NOT_DISPLAYED` for fields that are not directly visible.
