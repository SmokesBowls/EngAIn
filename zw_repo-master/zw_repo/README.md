# ZW Protocol — The Universal Language of AI

**ZW = Ziegel Wagga.** A protocol where **meaning > labels**. Schema-agnostic, noise-tolerant, and extensible mid‑stream.

> “Tell me what you want, however you want — I’ll figure it out.”

## Why ZW?
Traditional formats (JSON/XML) require rigid schemas. Real life is messy. ZW treats structure as **negotiable** and meaning as **primary**. You can rename keys, redefine vocabulary on the fly, and add new fields without breaking downstream systems.

## Key Principles
- **Schema-Agnostic:** Labels are hints; **intent is king**.
- **Extensible Mid-Stream:** Introduce new terms on the fly.
- **Vocabulary Remapping:** `meaning: left->a, right->b, combine->op`
- **Noise Tolerance:** Extra junk is ignored safely.
- **Deterministic Execution:** Loose in, precise out.

## Live Demo: ZW Calculator
A tiny proof-of-concept that accepts chaotic, human input and still computes correctly.

```bash
python tools/zw_calc_demo.py --demo
```

### Examples
```
ZiegelWagga: plus
alpha: 2
beta: 3
# → 5.0
```
```
meaning: left->a, right->b, combine->op
left: 10
right: 4
combine: minus
# → 6.0
```
```
compute: (3 + 5) * sqrt(16) - 7
# → 25.0
```
```
values: 1, 2, 3, 4, 5, 100
do: average
# → 19.166666...
```

## Repo Map
```
zw-protocol/
├─ LICENSE.md
├─ README.md
├─ CONTRIBUTING.md
├─ CODE_OF_CONDUCT.md
├─ tools/
│  └─ zw_calc_demo.py
├─ examples/
│  ├─ average_chaos.zw.txt
│  ├─ vocab_redefine.zw.txt
│  └─ power_op.zw.txt
└─ .gitignore
```

## Linking Other ZW Projects
Add your other repos under a **Projects** section here with short descriptions:
- ZW TTS (KittenTTS adapter) – `<link>`
- ZW Code Engine – `<link>`
- ZW Narrative Tools – `<link>`

## License
This project uses **ZWPPL-1.0** (Indie-First). Free for indie & small business. If your revenue ≥ **$250,000/year**, a commercial license is required. See **LICENSE.md**.
