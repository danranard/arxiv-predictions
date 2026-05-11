from __future__ import annotations

import argparse
import json
import math
import os
import random
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader, Dataset
try:
    from peft import LoraConfig, PeftModel, TaskType, get_peft_model
    from transformers import AutoModelForCausalLM, AutoTokenizer, get_cosine_schedule_with_warmup
except ImportError as exc:  # Allows `--help` to work on non-GPU/lightweight installs.
    LoraConfig = PeftModel = TaskType = get_peft_model = None  # type: ignore[assignment]
    AutoModelForCausalLM = AutoTokenizer = get_cosine_schedule_with_warmup = None  # type: ignore[assignment]
    IMPORT_ERROR = exc
else:
    IMPORT_ERROR = None


DEFAULT_MODEL = "Qwen/Qwen3-8B"
DEFAULT_TARGET_MODULES = ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]


@dataclass
class EncodedExample:
    input_ids: list[int]
    attention_mask: list[int]
    labels: list[int]
    prompt_tokens: int
    target_tokens: int
    source_index: int


class JsonlCompletionDataset(Dataset[dict[str, Any]]):
    def __init__(
        self,
        path: Path,
        tokenizer: Any,
        max_length: int,
        boundary_mode: str,
        strict: bool = True,
        limit: int | None = None,
    ) -> None:
        self.path = path
        self.tokenizer = tokenizer
        rows = read_jsonl(path)
        if limit is not None:
            rows = rows[:limit]
        self.examples = [
            encode_row(row, tokenizer, max_length, strict, index, boundary_mode)
            for index, row in enumerate(rows)
        ]

    def __len__(self) -> int:
        return len(self.examples)

    def __getitem__(self, index: int) -> dict[str, Any]:
        return asdict(self.examples[index])


def main() -> None:
    args = parse_args()
    if IMPORT_ERROR is not None:
        raise SystemExit(
            "Missing SFT dependency. Install GPU training requirements with "
            "`python -m pip install -r requirements_sft_gpu.txt`. "
            f"Original import error: {IMPORT_ERROR}"
        )
    set_seed(args.seed)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    tokenizer = AutoTokenizer.from_pretrained(args.model_name, trust_remote_code=True, use_fast=True)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token

    train_data = JsonlCompletionDataset(
        Path(args.train_jsonl),
        tokenizer,
        max_length=args.max_length,
        boundary_mode=args.boundary_mode,
        strict=not args.allow_truncate,
        limit=args.train_limit,
    )
    eval_data = JsonlCompletionDataset(
        Path(args.eval_jsonl),
        tokenizer,
        max_length=args.max_length,
        boundary_mode=args.boundary_mode,
        strict=not args.allow_truncate,
        limit=args.eval_limit,
    )

    if args.tokenize_only:
        summary = {
            "train": dataset_summary(train_data),
            "eval": dataset_summary(eval_data),
            "model_name": args.model_name,
            "max_length": args.max_length,
            "boundary_mode": args.boundary_mode,
        }
        (output_dir / "tokenize_only_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(summary, indent=2))
        return

    if not torch.cuda.is_available():
        raise SystemExit("CUDA is required for the training path. Use --tokenize-only for CPU/data checks.")

    dtype = torch.bfloat16 if args.bf16 else torch.float16
    model = AutoModelForCausalLM.from_pretrained(
        args.model_name,
        torch_dtype=dtype,
        trust_remote_code=True,
        attn_implementation=args.attn_implementation,
    )
    model.config.use_cache = False
    if args.gradient_checkpointing:
        model.gradient_checkpointing_enable()

    if args.init_adapter_path:
        model = PeftModel.from_pretrained(model, args.init_adapter_path, is_trainable=True)
    else:
        lora_config = LoraConfig(
            task_type=TaskType.CAUSAL_LM,
            r=args.lora_r,
            lora_alpha=args.lora_alpha,
            lora_dropout=args.lora_dropout,
            target_modules=parse_target_modules(args.target_modules),
            bias="none",
        )
        model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()
    device = torch.device("cuda")
    model.to(device)

    train_loader = DataLoader(
        train_data,
        batch_size=args.batch_size,
        shuffle=True,
        collate_fn=lambda batch: collate(batch, tokenizer.pad_token_id),
    )
    eval_loader = DataLoader(
        eval_data,
        batch_size=args.eval_batch_size,
        shuffle=False,
        collate_fn=lambda batch: collate(batch, tokenizer.pad_token_id),
    )
    trainable = [param for param in model.parameters() if param.requires_grad]
    optimizer = torch.optim.AdamW(trainable, lr=args.learning_rate, weight_decay=args.weight_decay)
    total_steps = math.ceil(len(train_loader) / args.grad_accum_steps) * args.epochs
    warmup_steps = int(total_steps * args.warmup_ratio)
    scheduler = get_cosine_schedule_with_warmup(optimizer, warmup_steps, total_steps)

    run_config = vars(args) | {
        "total_steps": total_steps,
        "warmup_steps": warmup_steps,
        "train_examples": len(train_data),
        "eval_examples": len(eval_data),
        "train_summary": dataset_summary(train_data),
        "eval_summary": dataset_summary(eval_data),
    }
    (output_dir / "run_config.json").write_text(json.dumps(run_config, indent=2) + "\n", encoding="utf-8")
    tokenizer.save_pretrained(output_dir / "tokenizer")

    global_step = 0
    optimizer.zero_grad(set_to_none=True)
    metrics_path = output_dir / "metrics.jsonl"
    start = time.time()

    for epoch in range(args.epochs):
        model.train()
        for local_step, batch in enumerate(train_loader, start=1):
            batch = move_batch(batch, device)
            with torch.amp.autocast("cuda", dtype=dtype):
                loss, loss_parts = clip2_loss(
                    model,
                    batch,
                    args.clip_nll,
                    args.loss_mode,
                    args.residual_nll_weight,
                )
                loss = loss / args.grad_accum_steps
            loss.backward()
            if local_step % args.grad_accum_steps == 0:
                if args.max_grad_norm > 0:
                    torch.nn.utils.clip_grad_norm_(trainable, args.max_grad_norm)
                optimizer.step()
                scheduler.step()
                optimizer.zero_grad(set_to_none=True)
                global_step += 1
                if global_step % args.log_every == 0:
                    record = {
                        "type": "train",
                        "epoch": epoch,
                        "step": global_step,
                        "elapsed_sec": round(time.time() - start, 2),
                        "lr": scheduler.get_last_lr()[0],
                        **loss_parts,
                    }
                    append_jsonl(metrics_path, record)
                    print(json.dumps(record))
                if args.eval_every and global_step % args.eval_every == 0:
                    eval_record = evaluate(
                        model,
                        eval_loader,
                        device,
                        dtype,
                        args.clip_nll,
                        args.loss_mode,
                        args.residual_nll_weight,
                    )
                    eval_record.update({"type": "eval", "epoch": epoch, "step": global_step})
                    append_jsonl(metrics_path, eval_record)
                    print(json.dumps(eval_record))
                if args.save_every and global_step % args.save_every == 0:
                    save_adapter(model, tokenizer, output_dir / f"checkpoint-step-{global_step}")

        eval_record = evaluate(
            model,
            eval_loader,
            device,
            dtype,
            args.clip_nll,
            args.loss_mode,
            args.residual_nll_weight,
        )
        eval_record.update({"type": "eval_epoch", "epoch": epoch, "step": global_step})
        append_jsonl(metrics_path, eval_record)
        print(json.dumps(eval_record))
        save_adapter(model, tokenizer, output_dir / f"checkpoint-epoch-{epoch + 1}")

    save_adapter(model, tokenizer, output_dir / "final_adapter")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train a Qwen3-8B LoRA with hard clip2 target-token loss.")
    parser.add_argument("--model-name", default=DEFAULT_MODEL)
    parser.add_argument("--train-jsonl", required=True)
    parser.add_argument("--eval-jsonl", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--init-adapter-path", help="Optional existing PEFT adapter to continue training.")
    parser.add_argument("--max-length", type=int, default=1024)
    parser.add_argument(
        "--boundary-mode",
        choices=["separate", "full_offset"],
        default="separate",
        help=(
            "separate tokenizes prompt and completion independently, matching the "
            "first LoRA trainer. full_offset tokenizes prompt+completion once "
            "and masks labels by completion character offsets, matching Fireworks "
            "echo-logprob scoring."
        ),
    )
    parser.add_argument("--allow-truncate", action="store_true")
    parser.add_argument("--train-limit", type=int)
    parser.add_argument("--eval-limit", type=int)
    parser.add_argument("--tokenize-only", action="store_true")
    parser.add_argument("--epochs", type=int, default=1)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--eval-batch-size", type=int, default=16)
    parser.add_argument("--grad-accum-steps", type=int, default=1)
    parser.add_argument("--learning-rate", type=float, default=2e-4)
    parser.add_argument("--weight-decay", type=float, default=0.0)
    parser.add_argument("--warmup-ratio", type=float, default=0.03)
    parser.add_argument("--clip-nll", type=float, default=2.0)
    parser.add_argument(
        "--loss-mode",
        choices=["hard_clip", "clip_plus_residual"],
        default="hard_clip",
        help="hard_clip optimizes min(NLL, clip_nll). clip_plus_residual adds residual_nll_weight * raw NLL.",
    )
    parser.add_argument(
        "--residual-nll-weight",
        type=float,
        default=0.0,
        help="Raw-NLL residual weight used when --loss-mode clip_plus_residual.",
    )
    parser.add_argument("--lora-r", type=int, default=32)
    parser.add_argument("--lora-alpha", type=int, default=64)
    parser.add_argument("--lora-dropout", type=float, default=0.05)
    parser.add_argument("--target-modules", default=",".join(DEFAULT_TARGET_MODULES))
    parser.add_argument("--bf16", action="store_true", default=True)
    parser.add_argument("--fp16", dest="bf16", action="store_false")
    parser.add_argument("--gradient-checkpointing", action="store_true", default=True)
    parser.add_argument("--no-gradient-checkpointing", dest="gradient_checkpointing", action="store_false")
    parser.add_argument("--attn-implementation", default="sdpa")
    parser.add_argument("--max-grad-norm", type=float, default=1.0)
    parser.add_argument("--log-every", type=int, default=10)
    parser.add_argument("--eval-every", type=int, default=0)
    parser.add_argument("--save-every", type=int, default=0)
    parser.add_argument("--seed", type=int, default=20260501)
    return parser.parse_args()


def read_jsonl(path: Path) -> list[dict[str, str]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def encode_row(
    row: dict[str, str],
    tokenizer: Any,
    max_length: int,
    strict: bool,
    index: int,
    boundary_mode: str,
) -> EncodedExample:
    prompt = row["prompt"]
    completion = row["completion"]
    if boundary_mode == "separate":
        prompt_ids = tokenizer(prompt, add_special_tokens=False)["input_ids"]
        target_ids = tokenizer(completion, add_special_tokens=False)["input_ids"]
        input_ids = prompt_ids + target_ids
        labels = [-100] * len(prompt_ids) + target_ids
        prompt_tokens = len(prompt_ids)
        target_tokens = len(target_ids)
    elif boundary_mode == "full_offset":
        full = prompt + completion
        encoded = tokenizer(full, add_special_tokens=False, return_offsets_mapping=True)
        input_ids = encoded["input_ids"]
        offsets = encoded["offset_mapping"]
        boundary = len(prompt)
        target_end = len(full)
        target_positions = [
            token_index
            for token_index, (start, _end) in enumerate(offsets)
            if boundary <= int(start) < target_end
        ]
        labels = [-100] * len(input_ids)
        for token_index in target_positions:
            labels[token_index] = input_ids[token_index]
        prompt_tokens = len(input_ids) - len(target_positions)
        target_tokens = len(target_positions)
        target_ids = [input_ids[token_index] for token_index in target_positions]
    else:
        raise ValueError(f"unknown boundary_mode={boundary_mode!r}")

    if not target_ids:
        raise ValueError(f"empty target at row {index}")
    total = len(input_ids)
    if total > max_length:
        if strict:
            raise ValueError(f"row {index} has {total} tokens > max_length={max_length}; use --allow-truncate if intended")
        if boundary_mode == "full_offset":
            raise ValueError("full_offset truncation is not implemented; increase --max-length instead")
        keep_prompt = max(0, max_length - len(target_ids))
        prompt_ids = input_ids[: len(input_ids) - len(target_ids)]
        prompt_ids = prompt_ids[-keep_prompt:]
        input_ids = prompt_ids + target_ids
        labels = [-100] * len(prompt_ids) + target_ids
        prompt_tokens = len(prompt_ids)
        target_tokens = len(target_ids)
        total = len(input_ids)
        if total > max_length:
            raise ValueError(f"target alone too long at row {index}: {len(target_ids)} tokens > {max_length}")
    return EncodedExample(
        input_ids=input_ids,
        attention_mask=[1] * len(input_ids),
        labels=labels,
        prompt_tokens=prompt_tokens,
        target_tokens=target_tokens,
        source_index=index,
    )


def collate(batch: list[dict[str, Any]], pad_token_id: int) -> dict[str, torch.Tensor]:
    max_len = max(len(item["input_ids"]) for item in batch)
    input_ids, attention_mask, labels, prompt_tokens, target_tokens, source_index = [], [], [], [], [], []
    for item in batch:
        pad_len = max_len - len(item["input_ids"])
        input_ids.append(item["input_ids"] + [pad_token_id] * pad_len)
        attention_mask.append(item["attention_mask"] + [0] * pad_len)
        labels.append(item["labels"] + [-100] * pad_len)
        prompt_tokens.append(item["prompt_tokens"])
        target_tokens.append(item["target_tokens"])
        source_index.append(item["source_index"])
    return {
        "input_ids": torch.tensor(input_ids, dtype=torch.long),
        "attention_mask": torch.tensor(attention_mask, dtype=torch.long),
        "labels": torch.tensor(labels, dtype=torch.long),
        "prompt_tokens": torch.tensor(prompt_tokens, dtype=torch.long),
        "target_tokens": torch.tensor(target_tokens, dtype=torch.long),
        "source_index": torch.tensor(source_index, dtype=torch.long),
    }


def clip2_loss(
    model: Any,
    batch: dict[str, torch.Tensor],
    clip_nll: float,
    loss_mode: str,
    residual_nll_weight: float,
) -> tuple[torch.Tensor, dict[str, float]]:
    outputs = model(input_ids=batch["input_ids"], attention_mask=batch["attention_mask"])
    logits = outputs.logits[:, :-1, :].contiguous()
    labels = batch["labels"][:, 1:].contiguous()
    valid = labels.ne(-100)
    safe_labels = labels.masked_fill(~valid, 0)
    token_ce = F.cross_entropy(
        logits.view(-1, logits.size(-1)),
        safe_labels.view(-1),
        reduction="none",
    ).view_as(labels)
    token_ce = token_ce * valid
    clipped_ce = torch.clamp(token_ce, max=clip_nll) * valid
    per_example_raw = token_ce.sum(dim=1) / valid.sum(dim=1).clamp_min(1)
    per_example_clip = clipped_ce.sum(dim=1) / valid.sum(dim=1).clamp_min(1)
    if loss_mode == "hard_clip":
        per_example_objective = per_example_clip
    elif loss_mode == "clip_plus_residual":
        per_example_objective = per_example_clip + residual_nll_weight * per_example_raw
    else:
        raise ValueError(f"unknown loss_mode={loss_mode!r}")
    loss = per_example_objective.mean()
    parts = {
        "loss_objective": float(loss.detach().cpu()),
        "loss_clip": float(per_example_clip.mean().detach().cpu()),
        "loss_raw": float(per_example_raw.mean().detach().cpu()),
        "target_tokens": int(valid.sum().detach().cpu()),
        "clipped_token_frac": float((token_ce.gt(clip_nll) & valid).sum().detach().cpu() / valid.sum().detach().cpu().clamp_min(1)),
    }
    return loss, parts


@torch.no_grad()
def evaluate(
    model: Any,
    loader: DataLoader,
    device: torch.device,
    dtype: torch.dtype,
    clip_nll: float,
    loss_mode: str,
    residual_nll_weight: float,
) -> dict[str, float]:
    model.eval()
    objective_losses, clip_losses, raw_losses, token_counts, clipped_counts = [], [], [], [], []
    for batch in loader:
        batch = move_batch(batch, device)
        with torch.amp.autocast("cuda", dtype=dtype):
            _loss, parts = clip2_loss(model, batch, clip_nll, loss_mode, residual_nll_weight)
        objective_losses.append(parts["loss_objective"])
        clip_losses.append(parts["loss_clip"])
        raw_losses.append(parts["loss_raw"])
        token_counts.append(parts["target_tokens"])
        clipped_counts.append(parts["clipped_token_frac"] * parts["target_tokens"])
    total_tokens = sum(token_counts)
    return {
        "loss_objective": weighted_mean(objective_losses, token_counts),
        "loss_clip": weighted_mean(clip_losses, token_counts),
        "loss_raw": weighted_mean(raw_losses, token_counts),
        "target_tokens": total_tokens,
        "clipped_token_frac": sum(clipped_counts) / max(total_tokens, 1),
    }


def weighted_mean(values: list[float], weights: list[int]) -> float:
    return float(sum(value * weight for value, weight in zip(values, weights)) / max(sum(weights), 1))


def move_batch(batch: dict[str, torch.Tensor], device: torch.device) -> dict[str, torch.Tensor]:
    return {key: value.to(device) for key, value in batch.items()}


def save_adapter(model: Any, tokenizer: Any, path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(path)
    tokenizer.save_pretrained(path)


def dataset_summary(data: JsonlCompletionDataset) -> dict[str, Any]:
    prompt_tokens = [row.prompt_tokens for row in data.examples]
    target_tokens = [row.target_tokens for row in data.examples]
    total_tokens = [len(row.input_ids) for row in data.examples]
    return {
        "examples": len(data),
        "prompt_tokens": length_stats(prompt_tokens),
        "target_tokens": length_stats(target_tokens),
        "total_tokens": length_stats(total_tokens),
    }


def length_stats(values: list[int]) -> dict[str, float]:
    ordered = sorted(values)
    if not ordered:
        return {}
    n = len(ordered)
    return {
        "min": ordered[0],
        "p10": ordered[int(0.1 * (n - 1))],
        "median": ordered[n // 2],
        "p90": ordered[int(0.9 * (n - 1))],
        "max": ordered[-1],
        "mean": round(sum(ordered) / n, 3),
    }


def parse_target_modules(value: str) -> list[str] | str:
    value = value.strip()
    if value == "all-linear":
        return value
    return [part.strip() for part in value.split(",") if part.strip()]


def append_jsonl(path: Path, row: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row) + "\n")


def set_seed(seed: int) -> None:
    random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


if __name__ == "__main__":
    main()
