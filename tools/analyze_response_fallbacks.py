from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class Row:
    entry_id: str
    comparisons: int
    final_true: int
    llm_calls: int
    sympy_success: int
    sympy_true: int
    sympy_false: int
    errors: int
    antlr4_errors: int


def _iter_jsonl(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)


def analyze_response_jsonl(path: Path) -> tuple[list[Row], dict[str, int]]:
    rows: list[Row] = []
    totals = {
        "entries": 0,
        "comparisons": 0,
        "final_true": 0,
        "llm_calls": 0,
        "sympy_success": 0,
        "sympy_true": 0,
        "sympy_false": 0,
        "errors": 0,
        "antlr4_errors": 0,
    }

    for obj in _iter_jsonl(path):
        entry_id = str(obj.get("id", ""))
        eq_results = obj.get("equivalency_results") or []
        if not isinstance(eq_results, list):
            eq_results = []

        comparisons = len(eq_results)
        final_true = 0
        llm_calls = 0
        sympy_success = 0
        sympy_true = 0
        sympy_false = 0
        errors = 0
        antlr4_errors = 0

        for r in eq_results:
            if not isinstance(r, dict):
                continue
            if r.get("final_result") is True:
                final_true += 1

            # equation_equivilancy.py では、SymPyがTrueのときだけLLM比較を呼ばない。
            # したがって llm_result が True/False (None以外) なら「LLM比較が走った」と見なせる。
            if r.get("llm_result") is not None:
                llm_calls += 1

            sympy_result = r.get("sympy_result")
            if sympy_result is True:
                sympy_success += 1
                sympy_true += 1
            elif sympy_result is False:
                sympy_success += 1
                sympy_false += 1

            err = r.get("error")
            if isinstance(err, str) and err:
                errors += 1
                if "antlr4" in err.lower():
                    antlr4_errors += 1

        rows.append(
            Row(
                entry_id=entry_id,
                comparisons=comparisons,
                final_true=final_true,
                llm_calls=llm_calls,
                sympy_success=sympy_success,
                sympy_true=sympy_true,
                sympy_false=sympy_false,
                errors=errors,
                antlr4_errors=antlr4_errors,
            )
        )

        totals["entries"] += 1
        totals["comparisons"] += comparisons
        totals["final_true"] += final_true
        totals["llm_calls"] += llm_calls
        totals["sympy_success"] += sympy_success
        totals["sympy_true"] += sympy_true
        totals["sympy_false"] += sympy_false
        totals["errors"] += errors
        totals["antlr4_errors"] += antlr4_errors

    return rows, totals


def _print_summary(totals: dict[str, int]) -> None:
    entries = totals["entries"]
    comparisons = totals["comparisons"]
    llm_calls = totals["llm_calls"]
    sympy_success = totals["sympy_success"]
    antlr4_errors = totals["antlr4_errors"]

    llm_rate = (llm_calls / comparisons) if comparisons else 0.0
    sympy_rate = (sympy_success / comparisons) if comparisons else 0.0
    antlr_rate = (antlr4_errors / comparisons) if comparisons else 0.0

    print("=== response.jsonl analysis ===")
    print(f"entries: {entries}")
    print(f"comparisons: {comparisons}")
    print(f"llm_calls: {llm_calls} (rate={llm_rate:.2%})")
    print(f"sympy_success: {sympy_success} (rate={sympy_rate:.2%})")
    print(f"antlr4_errors: {antlr4_errors} (rate={antlr_rate:.2%})")


def _write_csv(out_csv: Path, rows: list[Row]) -> None:
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(
            [
                "Entry ID",
                "Comparisons",
                "Final True",
                "LLM Calls",
                "SymPy Success",
                "SymPy True",
                "SymPy False",
                "Errors",
                "ANTLR4 Errors",
            ]
        )
        for r in rows:
            w.writerow(
                [
                    r.entry_id,
                    r.comparisons,
                    r.final_true,
                    r.llm_calls,
                    r.sympy_success,
                    r.sympy_true,
                    r.sympy_false,
                    r.errors,
                    r.antlr4_errors,
                ]
            )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="response.jsonl を解析し、同値判定のLLMフォールバック回数（llm_result非null）などを集計します。"
    )
    parser.add_argument(
        "response_jsonl",
        type=str,
        help="解析対象の response.jsonl パス",
    )
    parser.add_argument(
        "--out-csv",
        type=str,
        default="",
        help="問題ごとの集計をCSVに出力する場合のパス（省略可）",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=20,
        help="LLMフォールバック回数が多い順に表示する件数（デフォルト20）",
    )
    args = parser.parse_args()

    path = Path(args.response_jsonl)
    if not path.exists():
        raise FileNotFoundError(f"Not found: {path}")

    rows, totals = analyze_response_jsonl(path)
    _print_summary(totals)

    if args.top > 0:
        print(f"--- top {args.top} by llm_calls ---")
        for r in sorted(rows, key=lambda x: x.llm_calls, reverse=True)[: args.top]:
            print(
                f"{r.entry_id}: llm_calls={r.llm_calls}, comparisons={r.comparisons}, "
                f"sympy_success={r.sympy_success}, antlr4_errors={r.antlr4_errors}"
            )

    if args.out_csv:
        out_csv = Path(args.out_csv)
        _write_csv(out_csv, rows)
        print(f"CSV written: {out_csv}")


if __name__ == "__main__":
    main()


