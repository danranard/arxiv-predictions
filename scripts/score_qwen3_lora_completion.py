from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Any

torch = None
F = None
PeftModel = None
AutoModelForCausalLM = None
AutoTokenizer = None


def main() -> None:
    args = parse_args()
    load_model_dependencies()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    keys = load_keys(Path(args.keys_json)) if args.keys_json else None
    rows = []
    for row in read_jsonl(Path(args.examples_jsonl)):
        if args.split.lower() != "all" and row.get("split") != args.split:
            continue
        key = (str(row["paper_id"]), int(row["cut_id"]))
        if keys is not None and key not in keys:
            continue
        rows.append(row)
    rows.sort(key=lambda r: (str(r["paper_id"]), int(r["cut_id"]), int(r.get("dataset_row_index", -1))))
    if args.limit is not None:
        rows = rows[: args.limit]
    if not rows:
        raise SystemExit("No rows selected.")

    tokenizer = AutoTokenizer.from_pretrained(args.model_name, trust_remote_code=True, use_fast=True)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token

    dtype = torch.bfloat16 if args.bf16 else torch.float16
    model = AutoModelForCausalLM.from_pretrained(
        args.model_name,
        torch_dtype=dtype,
        trust_remote_code=True,
        attn_implementation=args.attn_implementation,
    )
    if args.adapter_path:
        model = PeftModel.from_pretrained(model, args.adapter_path)
    model.eval()
    model.to("cuda")

    records = []
    token_records = []
    with torch.no_grad():
        for i, row in enumerate(rows):
            rec, toks = score_row(row, model, tokenizer, dtype, args.max_length, i, args.boundary_mode)
            records.append(rec)
            if args.write_token_logprobs:
                token_records.extend(toks)
            if args.progress_every and (i + 1) % args.progress_every == 0:
                print(json.dumps({"type": "progress", "done": i + 1, "total": len(rows)}), flush=True)

    write_csv(output_dir / "completion_scores.csv", records)
    if args.write_token_logprobs:
        write_csv(output_dir / "completion_target_token_logprobs.csv", token_records)

    summary = summarize(records)
    summary.update(
        {
            "model_name": args.model_name,
            "adapter_path": args.adapter_path,
            "examples_jsonl": args.examples_jsonl,
            "keys_json": args.keys_json,
            "split": args.split,
            "n": len(records),
        }
    )
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


def load_model_dependencies() -> None:
    global torch, F, PeftModel, AutoModelForCausalLM, AutoTokenizer
    try:
        import torch as torch_mod
        import torch.nn.functional as f_mod
        from peft import PeftModel as peft_model_cls
        from transformers import AutoModelForCausalLM as auto_model_cls
        from transformers import AutoTokenizer as auto_tokenizer_cls
    except ImportError as exc:
        raise SystemExit(
            "Missing SFT scoring dependency. Install the GPU audit extras with "
            "`python -m pip install -r requirements_sft_gpu.txt`. "
            f"Original import error: {exc}"
        ) from exc
    torch = torch_mod
    F = f_mod
    PeftModel = peft_model_cls
    AutoModelForCausalLM = auto_model_cls
    AutoTokenizer = auto_tokenizer_cls


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Score raw completion logprobs with Qwen, optionally with a LoRA adapter.")
    parser.add_argument("--model-name", default="Qwen/Qwen3-8B")
    parser.add_argument("--adapter-path")
    parser.add_argument("--examples-jsonl", required=True)
    parser.add_argument("--keys-json")
    parser.add_argument("--split", default="test")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--max-length", type=int, default=1024)
    parser.add_argument("--bf16", action="store_true", default=True)
    parser.add_argument("--fp16", dest="bf16", action="store_false")
    parser.add_argument("--attn-implementation", default="sdpa")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--progress-every", type=int, default=10)
    parser.add_argument("--write-token-logprobs", action="store_true")
    parser.add_argument(
        "--boundary-mode",
        choices=["separate", "full_offset"],
        default="separate",
        help=(
            "separate tokenizes prompt and completion independently, matching the "
            "original LoRA trainer. full_offset tokenizes prompt+completion once "
            "and scores tokens whose offsets begin inside completion, matching the "
            "Fireworks echo-logprob scorer more closely."
        ),
    )
    return parser.parse_args()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def load_keys(path: Path) -> set[tuple[str, int]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return {(str(row["paper_id"]), int(row["cut_id"])) for row in data["keys"]}


def score_row(
    row: dict[str, Any],
    model: Any,
    tokenizer: Any,
    dtype: torch.dtype,
    max_length: int,
    ordinal: int,
    boundary_mode: str,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    prompt = row["prompt"]
    completion = row["completion"]
    if boundary_mode == "separate":
        prompt_ids = tokenizer(prompt, add_special_tokens=False)["input_ids"]
        target_ids = tokenizer(completion, add_special_tokens=False)["input_ids"]
        target_positions = list(range(len(prompt_ids), len(prompt_ids) + len(target_ids)))
    elif boundary_mode == "full_offset":
        full = prompt + completion
        encoded = tokenizer(full, add_special_tokens=False, return_offsets_mapping=True)
        input_ids_list = encoded["input_ids"]
        offsets = encoded["offset_mapping"]
        boundary = len(prompt)
        target_end = len(full)
        target_positions = [
            index
            for index, (start, _end) in enumerate(offsets)
            if boundary <= int(start) < target_end
        ]
        target_ids = [input_ids_list[index] for index in target_positions]
        prompt_ids = tokenizer(prompt, add_special_tokens=False)["input_ids"]
    else:
        raise ValueError(f"unknown boundary_mode={boundary_mode!r}")

    if not target_ids:
        raise ValueError(f"empty target for {row.get('paper_id')} cut {row.get('cut_id')}")
    input_ids_list = (
        prompt_ids + target_ids
        if boundary_mode == "separate"
        else tokenizer(prompt + completion, add_special_tokens=False)["input_ids"]
    )
    if len(input_ids_list) > max_length:
        raise ValueError(
            f"row too long: full token length {len(input_ids_list)} > max_length {max_length}"
        )
    input_ids = torch.tensor([input_ids_list], dtype=torch.long, device="cuda")
    attention_mask = torch.ones_like(input_ids)
    with torch.amp.autocast("cuda", dtype=dtype):
        outputs = model(input_ids=input_ids, attention_mask=attention_mask)
        logits = outputs.logits[:, :-1, :]
        labels = input_ids[:, 1:]
        log_probs = F.log_softmax(logits.float(), dim=-1)
        token_logps = log_probs.gather(-1, labels.unsqueeze(-1)).squeeze(-1)
    # token_logps[j - 1] is the logprob assigned to input_ids[j].
    target_logps = [
        float(token_logps[0, position - 1].detach().cpu())
        for position in target_positions
        if position > 0
    ]
    if len(target_logps) != len(target_ids):
        raise AssertionError(f"target logprob length mismatch: {len(target_logps)} vs {len(target_ids)}")

    raw = sum(target_logps) / len(target_logps)
    clip2 = sum(max(lp, -2.0) for lp in target_logps) / len(target_logps)
    clip3 = sum(max(lp, -3.0) for lp in target_logps) / len(target_logps)
    clip5 = sum(max(lp, -5.0) for lp in target_logps) / len(target_logps)
    rec = {
        "ordinal": ordinal,
        "split": row.get("split"),
        "dataset_row_index": row.get("dataset_row_index"),
        "paper_id": row.get("paper_id"),
        "equation_index": row.get("equation_index"),
        "cut_id": row.get("cut_id"),
        "operator": row.get("operator"),
        "operator_class": row.get("operator_class"),
        "env": row.get("env"),
        "y_len": row.get("y_len"),
        "budget_chars": row.get("budget_chars"),
        "prompt_chars": len(prompt),
        "target_chars": len(completion),
        "prompt_tokens": len(prompt_ids),
        "target_tokens": len(target_ids),
        "boundary_mode": boundary_mode,
        "raw_mean_logprob": raw,
        "clip2_mean_logprob": clip2,
        "clip3_mean_logprob": clip3,
        "clip5_mean_logprob": clip5,
        "raw_nll": -raw,
        "clip2_nll": -clip2,
        "clip3_nll": -clip3,
        "clip5_nll": -clip5,
        "clipped2_token_frac": sum(1 for lp in target_logps if lp < -2.0) / len(target_logps),
    }
    toks = [
        {
            "ordinal": ordinal,
            "paper_id": row.get("paper_id"),
            "cut_id": row.get("cut_id"),
            "token_index": j,
            "full_token_position": target_positions[j],
            "token_id": tok_id,
            "token_text": tokenizer.decode([tok_id]),
            "logprob": lp,
            "clip2_logprob": max(lp, -2.0),
        }
        for j, (tok_id, lp) in enumerate(zip(target_ids, target_logps))
    ]
    return rec, toks


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def summarize(records: list[dict[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key in ["raw_mean_logprob", "clip2_mean_logprob", "clip3_mean_logprob", "clip5_mean_logprob"]:
        vals = [float(row[key]) for row in records]
        out[key] = stats(vals)
    return out


def stats(vals: list[float]) -> dict[str, float]:
    n = len(vals)
    mean = sum(vals) / n
    stdev = math.sqrt(sum((x - mean) ** 2 for x in vals) / (n - 1)) if n > 1 else 0.0
    return {
        "n": n,
        "mean": mean,
        "stdev": stdev,
        "stderr": stdev / math.sqrt(n) if n else float("nan"),
        "median": sorted(vals)[n // 2],
    }


if __name__ == "__main__":
    main()
