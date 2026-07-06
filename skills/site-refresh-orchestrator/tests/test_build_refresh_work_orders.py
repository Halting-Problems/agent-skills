from __future__ import annotations

import importlib.util
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "build_refresh_work_orders.py"
spec = importlib.util.spec_from_file_location("build_refresh_work_orders", MODULE_PATH)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_followup_candidate_routes_to_existing_post_upgrade():
    candidate = {
        "candidate_id": "atomic-arch-aur-compromise-followup",
        "title": "400+ AUR Packages Hijacked: What the Atomic Arch Campaign Means for Supply-Chain Security",
        "candidate_threat_classes": ["follow-up-analysis"],
        "dedupe_keys": ["campaign:atomic-arch", "ecosystem:aur"],
        "starting_sources": [
            {"url": "https://www.stepsecurity.io/blog/400-aur-packages-hijacked-atomic-arch-campaign"}
        ],
    }
    existing = {
        "urls": set(),
        "slugs": {"atomic-arch-aur-compromise"},
        "dedupe_keys": {"campaign:atomic-arch"},
        "event_ids": set(),
        "posts": [
            {
                "slug": "atomic-arch-aur-compromise",
                "title": "Atomic Arch: AUR Package Takeover Delivers Infostealers and eBPF Rootkits",
                "date": "2026-06-12",
                "urls": set(),
                "dedupe_keys": {"campaign:atomic-arch"},
            }
        ],
    }

    classification = module.classify_candidate(candidate, existing)

    assert classification["disposition"] == "update_existing"
    assert classification["canonical_slug"] == "atomic-arch-aur-compromise"

    work_orders = module.make_work_orders([candidate], existing)
    worker = work_orders["site_refresh_result"]["spawned_site_workers"][0]
    assert worker["recommended_mode"] == "existing_post_upgrade"
    assert worker["canonical_existing_slug"] == "atomic-arch-aur-compromise"


def test_exact_same_candidate_stays_already_reported_when_no_new_sources():
    candidate = {
        "candidate_id": "glasswasm-open-vsx-extensions",
        "title": "GlassWASM: WebAssembly Malware Found in Trojanized Open VSX Extensions",
        "dedupe_keys": ["campaign:glasswasm"],
        "starting_sources": [
            {"url": "https://socket.dev/blog/glasswasm-malware-open-vsx-extensions"}
        ],
    }
    existing = {
        "urls": {"https://socket.dev/blog/glasswasm-malware-open-vsx-extensions"},
        "slugs": {"glasswasm-open-vsx-extensions"},
        "dedupe_keys": {"campaign:glasswasm"},
        "event_ids": set(),
        "posts": [
            {
                "slug": "glasswasm-open-vsx-extensions",
                "title": "GlassWASM: Trojanized Open VSX Extensions Used TinyGo WebAssembly and Solana Memo C2",
                "date": "2026-06-20",
                "urls": {"https://socket.dev/blog/glasswasm-malware-open-vsx-extensions"},
                "dedupe_keys": {"campaign:glasswasm"},
            }
        ],
    }

    classification = module.classify_candidate(candidate, existing)

    assert classification["disposition"] == "already_reported"


def test_new_candidate_without_match_stays_new():
    candidate = {
        "candidate_id": "brand-new-incident",
        "title": "Totally New Incident",
        "dedupe_keys": ["package:brand-new"],
        "starting_sources": [{"url": "https://example.com/new"}],
    }
    existing = {"urls": set(), "slugs": set(), "dedupe_keys": set(), "event_ids": set(), "posts": []}

    classification = module.classify_candidate(candidate, existing)

    assert classification["disposition"] == "new"
    assert classification["canonical_slug"] == ""


def test_worker_prompt_requires_modular_plan_and_agency_reviews():
    candidate = {
        "candidate_id": "modular-test",
        "title": "Modular Test",
        "dedupe_keys": ["package:modular-test"],
        "starting_sources": [{"url": "https://example.com/modular"}],
    }
    existing = {"urls": set(), "slugs": set(), "dedupe_keys": set(), "event_ids": set(), "posts": []}

    work_orders = module.make_work_orders([candidate], existing)
    prompt = work_orders["site_refresh_result"]["spawned_site_workers"][0]["prompt"]

    assert "site_worker_plan.py" in prompt
    assert "validate_site_worker_plan.py" in prompt
    assert "/home/sam/agency-agents" in prompt
    assert "agent-pipeline-critique-questions.md" in prompt
    assert "Next.js/Postgres" in prompt
    assert "Astro" in prompt
    assert "D1" in prompt
