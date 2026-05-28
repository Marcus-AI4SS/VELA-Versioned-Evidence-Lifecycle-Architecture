# agent-browser Templates



## When to Promote a Task to agent-browser



Switch from `chrome-devtools` to the template when:



- the page requires repeated clicking or scrolling

- multiple visible cards must be opened in sequence

- the user wants repeatable capture artifacts

- the task needs session persistence

- a platform case should be rerun later with the same local workflow



## Template Entry Script



Primary template:



- `scripts/run-social-platform-agent-browser-template.ps1`



Workspace wrapper:



- `<VELA_RUNTIME_ROOT>\skills\scripts\run-social-platform-agent-browser-template.ps1`



## Common Invocations



### Douyin video


```powershell

pwsh -ExecutionPolicy Bypass -File "<VELA_RUNTIME_ROOT>\skills\scripts\run-social-platform-agent-browser-template.ps1" -Platform douyin -ArtifactType video -Url "https://www.douyin.com/video/..."

```



### Bilibili video



```powershell

pwsh -ExecutionPolicy Bypass -File "<VELA_RUNTIME_ROOT>\skills\scripts\run-social-platform-agent-browser-template.ps1" -Platform bilibili -ArtifactType video -Url "https://www.bilibili.com/video/..."

```



### WeChat public article



```powershell

pwsh -ExecutionPolicy Bypass -File "<VELA_RUNTIME_ROOT>\skills\scripts\run-social-platform-agent-browser-template.ps1" -Platform wechat -ArtifactType article -Url "https://mp.weixin.qq.com/s/..."

```



## Default Artifacts



Each run writes:



- `metadata.json`

- `snapshot-interactive.json`

- `screenshot.png`

- optional `state.json`



under the local outputs directory for later audit.
