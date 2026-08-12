import datetime

from django.core.management.base import BaseCommand

from ai_assistant.rag_evaluation import run_rag_evaluation
from triage.evaluation import run_rule_engine_evaluation, summarize
from triage.llm_evaluation import run_llm_evaluation


def _rule_engine_section(results):
    lines = ["## Rule Engine Evaluation (Layer 1)", "", "```"]
    lines.append(f"{'Case':<40} {'Expected':<12} {'Actual':<12} {'Result'}")
    lines.append("-" * 80)
    for r in results:
        mark = "PASS" if r["passed"] else "FAIL"
        lines.append(f"{r['description']:<40} {r['expected_urgency']:<12} {r['actual_urgency']:<12} {mark}")
    summary = summarize(results)
    lines.append("")
    lines.append(f"Accuracy: {summary['passed']}/{summary['total']} ({summary['accuracy']:.0%})")
    lines.append("```")
    return lines, summary


def _llm_section(metrics_by_provider):
    lines = ["## LLM Evaluation (Layer 3)", "", "```"]
    lines.append(f"{'Provider':<10} {'Success':<10} {'Failure':<10} {'Timeout':<10} {'Invalid':<10} {'Avg ms':<10} {'Min ms':<10} {'Max ms'}")
    lines.append("-" * 90)
    for provider, m in metrics_by_provider.items():
        lines.append(
            f"{provider:<10} {m['success_rate']:<10.0%} {m['failure_rate']:<10.0%} {m['timeout_rate']:<10.0%} "
            f"{m['invalid_response_rate']:<10.0%} {m['avg_latency_ms']:<10.0f} {m['min_latency_ms']:<10.0f} {m['max_latency_ms']:.0f}"
        )
        for c in m["calls"]:
            err = f" ({c['error']})" if c["error"] else ""
            lines.append(f"  - [{c['outcome']}] {c['latency_ms']:.0f}ms{err}")
    lines.append("```")
    return lines


def _rag_section(results):
    lines = ["## RAG Authorization Evaluation", "", "```"]
    lines.append(f"{'Case':<40} {'Expected':<10} {'Actual':<16} {'Result'}")
    lines.append("-" * 80)
    for r in results:
        mark = "PASS" if r["passed"] else "FAIL"
        lines.append(f"{r['description']:<40} {r['expected']:<10} {r['actual']:<16} {mark}")
    lines.append("")
    all_passed = all(r["passed"] for r in results)
    lines.append("RAG must never bypass authorization: " + ("HOLDS" if all_passed else "VIOLATION DETECTED"))
    lines.append("```")
    return lines, all_passed


class Command(BaseCommand):
    help = (
        "Runs the Phase 12 AI evaluation suite: rule-engine test matrix, live LLM "
        "latency/reliability metrics (Ollama vs Groq), and the RAG cross-patient "
        "authorization matrix. Read-only — the RAG section uses a rolled-back transaction "
        "and the LLM section makes no database writes at all."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--output", default=None,
            help="Optional path to also write the report as Markdown (e.g. docs/ai_evaluation_report.md).",
        )

    def handle(self, *args, **options):
        report_lines = [
            "# AI Evaluation Report",
            "",
            f"Generated: {datetime.datetime.now().isoformat(timespec='seconds')}",
            "",
        ]

        self.stdout.write("Running rule engine evaluation...")
        rule_results = run_rule_engine_evaluation()
        rule_lines, rule_summary = _rule_engine_section(rule_results)
        report_lines += rule_lines + [""]

        self.stdout.write("Running LLM evaluation (live network calls, may take a while)...")
        llm_metrics = run_llm_evaluation()
        report_lines += _llm_section(llm_metrics) + [""]

        self.stdout.write("Running RAG authorization evaluation...")
        rag_results = run_rag_evaluation()
        rag_lines, rag_ok = _rag_section(rag_results)
        report_lines += rag_lines + [""]

        report = "\n".join(report_lines)
        self.stdout.write("\n" + report + "\n")

        if options["output"]:
            output_path = options["output"]
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(report + "\n")
            self.stdout.write(self.style.SUCCESS(f"Report written to {output_path}"))

        if rule_summary["failed"] or not rag_ok:
            self.stdout.write(self.style.ERROR("One or more evaluation cases FAILED — see report above."))
        else:
            self.stdout.write(self.style.SUCCESS("All deterministic evaluation cases passed."))
