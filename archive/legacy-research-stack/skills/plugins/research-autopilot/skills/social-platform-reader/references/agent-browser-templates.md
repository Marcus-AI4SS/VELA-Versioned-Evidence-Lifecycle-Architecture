# agent-browser Templates

## When to Promote a Task to agent-browser

Switch from `chrome-devtools` to the template when:

- the page requires repeated clicking or scrolling
- multiple visible cards must be opened in sequence
- the user wants repeatable capture artifacts
- the task needs session persistence
- a platform case should be rerun later with the same local workflow

## Template Entry Script

This public repository does not ship an agent-browser runner script by default.
Use agent-browser directly, or add a local project wrapper only after reviewing the target platform and output path.

Optional local wrapper name:

- `<PROJECT_ROOT>/scripts/run-social-platform-agent-browser-template.ps1`

## Common Invocations

### Douyin video

```powershell
agent-browser open "https://www.douyin.com/video/..."
```

### Bilibili video

```powershell
agent-browser open "https://www.bilibili.com/video/..."
```

### WeChat public article

```powershell
agent-browser open "https://mp.weixin.qq.com/s/..."
```

## Default Artifacts

Each run writes:

- `metadata.json`
- `snapshot-interactive.json`
- `screenshot.png`
- optional `state.json`

under the local outputs directory for later audit.
