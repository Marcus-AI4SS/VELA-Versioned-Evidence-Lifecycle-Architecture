# Privacy Boundaries

VELA is designed as a public workflow package. It keeps reusable rules, schemas, validators, examples, and documentation in the repository, while user data stays in the user's own project and runtime.

## Excluded By Default

- credentials, tokens, cookies, and SSH keys
- account sessions and browser state
- Codex trust state and plugin caches
- runtime caches, generated outputs, and machine-specific repair scripts
- personal notes, private datasets, and unpublished project material

## Portable Defaults

- use relative paths or documented placeholders
- keep examples free of user names and absolute machine paths
- keep integrations opt-in when they require user accounts or local databases
- keep research rules and workflow structure reusable across machines

## Public Contract

What stays public:

- workflow structure
- schemas and validators
- install scripts and runtime manifests
- public examples and docs
- reusable skill and routing metadata

What stays outside the repository:

- secrets
- private project material
- personal account state
- generated runtime data
