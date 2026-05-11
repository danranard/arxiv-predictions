# Fresh40 Scaffold-Aware Judge SFT: Nano Low/Medium/High v0

This is a higher-volume sibling of the nano-low canonical SFT. It trains
on `model_direct_y_3` forecast notes from nano low, medium, and high on
train papers only, then leaves GPT-5.5 lanes as cleaner held-out
benchmark-style probes.

Settings:
- Models: `gpt54_nano_low,gpt54_nano_medium,gpt54_nano_high`.
- X base chars: `2000`.
- X tail chars: `2000`.
- Z budget chars: `1000`.
- Loss should be raw target-token NLL.
- Boundary mode should be `full_offset`.

Counts:
```json
{
  "rows": 1953,
  "cuts": 651,
  "by_split": {
    "eval": 975,
    "train": 978
  },
  "by_model": {
    "gpt54_nano_high": 651,
    "gpt54_nano_low": 651,
    "gpt54_nano_medium": 651
  },
  "by_split_model": {
    "eval::gpt54_nano_high": 325,
    "eval::gpt54_nano_low": 325,
    "eval::gpt54_nano_medium": 325,
    "train::gpt54_nano_high": 326,
    "train::gpt54_nano_low": 326,
    "train::gpt54_nano_medium": 326
  }
}
```
