# himself65-trade

> [!WARNING]
> This project is for educational and informational purposes only. Nothing here constitutes financial advice. Always do your own research and consult a qualified financial advisor before making investment decisions.

A personal Claude Code plugin marketplace housing one options-trading skill (`himself65-trade`) — backed by a curated library of 24 pitfalls and prior case studies (INTC, Mag-7, APP, NOK, TSEM, CBRS, SNOW). Layout follows the [`himself65/finance-skills`](https://github.com/himself65/finance-skills) convention.

## Quick Start

### Kimi Code — Install the plugin

```bash
/plugins install https://github.com/CompaCompu/himself65-trade-skills-for-kimi/archive/refs/tags/v1.7.1-kimi.zip
```

Then start a new session (`/new`) to load the skill.

> **Why the `.zip` URL?** Kimi Code's GitHub repo install path has bugs with release tag resolution (`refs/tags/` → 400) and branch fallback (`zip/HEAD` → truncated). The archive zip URL bypasses all GitHub-specific logic and is treated as a plain zip download — the stable, documented install path.

### Claude Code — Install the plugin

```bash
npx plugins add himself65/trade-skills
```

### Claude Code — Install just the skill

```bash
npx skills add himself65/trade-skills
```

### Other agents

```bash
npx skills add himself65/trade-skills -a <agent-name>
```

### Local development install (from a clone)

```bash
git clone https://github.com/himself65/trade-skills.git ~/trade-skills
ln -s ~/trade-skills/plugins/trade/skills/trade ~/.claude/skills/trade
```

## Available Skills

### himself65-trade (`himself65-trade`)

Multi-leg options trading assistant with concrete strikes, IV-aware structures, and probability-weighted scenarios.

| Skill | Description |
|---|---|
| [himself65-trade](plugins/himself65-trade/skills/himself65-trade/) | Options trading knowledge base — 24 pitfalls + INTC / Mag-7 / APP / NOK / TSEM / CBRS / SNOW case studies + structure-to-regime framework. Lazy-loaded. |

## License

MIT
