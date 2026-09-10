#!/usr/bin/env python3
"""Nomes canônicos, ledger e reuso de worktree — git-activity."""

from __future__ import annotations

import unittest
from datetime import datetime
from pathlib import Path

import status as mod


class NamesTest(unittest.TestCase):
    def test_stamp_is_yyyymmdd_hhmm(self) -> None:
        self.assertEqual(
            mod.activity_stamp(datetime(2026, 9, 10, 9, 55)),
            "20260910-0955",
        )

    def test_branch_and_folder_date_first(self) -> None:
        stamp = "20260910-0955"
        self.assertEqual(
            mod.branch_name("feature", stamp, "git-activity-flow"),
            "feature/20260910-0955-git-activity-flow",
        )
        self.assertEqual(
            mod.worktree_folder(stamp=stamp, kind="feature", slug="git-activity-flow"),
            "20260910-0955-feature-git-activity-flow",
        )
        self.assertEqual(
            mod.worktree_folder(
                stamp=stamp,
                kind="feature",
                slug="git-activity-flow",
                repo="ai-harness",
            ),
            "20260910-0955-ai-harness-feature-git-activity-flow",
        )

    def test_delivery_branch_has_optional_develop_suffix(self) -> None:
        self.assertEqual(
            mod.delivery_branch("20260910-0955", "git-activity-flow"),
            "delivery/20260910-0955-git-activity-flow",
        )
        self.assertEqual(
            mod.delivery_branch("20260910-0955", "git-activity-flow", develop=True),
            "delivery/20260910-0955-git-activity-flow-develop",
        )

    def test_parse_strips_develop_from_delivery_slug(self) -> None:
        parsed = mod.parse_activity_branch(
            "delivery/20260910-0955-git-activity-flow-develop"
        )
        self.assertEqual(
            parsed,
            {
                "kind": "delivery",
                "stamp": "20260910-0955",
                "slug": "git-activity-flow",
                "develop": True,
            },
        )

    def test_reject_invalid_slug(self) -> None:
        with self.assertRaises(ValueError):
            mod.branch_name("feature", "20260910-0955", "Git Activity")


class WorktreeParseTest(unittest.TestCase):
    PORCELAIN = """\
worktree /repo/ai-harness
HEAD abc111
branch refs/heads/main

worktree /repo/worktrees/20260910-0955-ai-harness-feature-git-activity-flow
HEAD def222
branch refs/heads/feature/20260910-0955-git-activity-flow
"""

    def test_parse_porcelain_skips_nothing_raw(self) -> None:
        trees = mod.parse_worktree_porcelain(self.PORCELAIN)
        self.assertEqual(len(trees), 2)
        self.assertEqual(trees[1].branch, "feature/20260910-0955-git-activity-flow")
        self.assertEqual(trees[1].sha, "def222")


class EstadoTest(unittest.TestCase):
    def test_sem_pr_aberta(self) -> None:
        self.assertEqual(
            mod.classify_estado(has_worktree=True, pr_prod=None, pr_develop=None),
            "aberta",
        )

    def test_pr_open(self) -> None:
        pr = mod.PullRequest(
            number=1,
            url="https://example.com/1",
            state="OPEN",
            base="main",
            head="delivery/20260910-0955-git-activity-flow",
            merged=False,
        )
        self.assertEqual(
            mod.classify_estado(has_worktree=True, pr_prod=pr, pr_develop=None),
            "pr-aberta",
        )

    def test_merged_ainda_no_disco(self) -> None:
        pr = mod.PullRequest(
            number=4,
            url="https://example.com/4",
            state="MERGED",
            base="main",
            head="delivery/20260910-0955-git-activity-flow",
            merged=True,
        )
        self.assertEqual(
            mod.classify_estado(has_worktree=True, pr_prod=pr, pr_develop=None),
            "mergeada",
        )

    def test_merged_sem_pasta_e_podada(self) -> None:
        pr = mod.PullRequest(
            number=4,
            url="https://example.com/4",
            state="MERGED",
            base="main",
            head="delivery/20260910-0955-git-activity-flow",
            merged=True,
        )
        self.assertEqual(
            mod.classify_estado(has_worktree=False, pr_prod=pr, pr_develop=None),
            "podada",
        )


class LedgerTest(unittest.TestCase):
    def test_roundtrip_and_upsert_other_repo(self) -> None:
        row = mod.ActivityRow(
            repo="ai-harness",
            pasta="20260910-0955-ai-harness-feature-foo",
            kind="feature",
            slug="foo",
            branch="feature/20260910-0955-foo",
            sha="abc1234",
            pr_prod="https://example.com/1",
            merge_prod="não",
            pr_develop="—",
            merge_develop="—",
            estado="pr-aberta",
        )
        rendered = mod.render_ledger("ai-harness", [row], updated="2026-09-10 09:55")
        parsed = mod.parse_ledger(rendered)
        self.assertEqual(parsed["ai-harness"][0].slug, "foo")
        self.assertEqual(parsed["ai-harness"][0].estado, "pr-aberta")

        other = "# Atividades\n\n## mouse\n\n| pasta | kind |\n| --- | --- |\n"
        merged = mod.upsert_section(other, "ai-harness", rendered)
        self.assertIn("## mouse", merged)
        self.assertIn("## ai-harness", merged)

    def test_reconcile_keeps_merged_after_prune(self) -> None:
        old = mod.ActivityRow(
            repo="ai-harness",
            pasta="20260910-0800-ai-harness-feature-foo",
            kind="feature",
            slug="foo",
            branch="feature/20260910-0800-foo",
            sha="deadbee",
            pr_prod="https://example.com/9",
            merge_prod="sim",
            pr_develop="—",
            merge_develop="—",
            estado="mergeada",
        )
        pr = mod.PullRequest(
            number=9,
            url="https://example.com/9",
            state="MERGED",
            base="main",
            head="delivery/20260910-0800-foo",
            merged=True,
        )
        out = mod.reconcile([old], live=[], prs=[pr])
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].estado, "podada")

    def test_find_existing_by_slug(self) -> None:
        trees = mod.parse_worktree_porcelain(WorktreeParseTest.PORCELAIN)
        found = mod.find_existing_activity(trees, slug="git-activity-flow")
        self.assertIsNotNone(found)
        assert found is not None
        self.assertTrue(found.path.endswith("git-activity-flow"))
        self.assertIsNone(mod.find_existing_activity(trees, slug="outro"))

    def test_legacy_feature_matches_delivery_pr(self) -> None:
        pr = mod.PullRequest(
            number=3,
            url="https://example.com/3",
            state="MERGED",
            base="main",
            head="delivery/agent-birth-runtime",
            merged=True,
        )
        prod, develop = mod.match_prs([pr], "feature/agent-birth-runtime")
        self.assertIsNotNone(prod)
        assert prod is not None
        self.assertTrue(prod.merged)
        self.assertIsNone(develop)


class PruneTest(unittest.TestCase):
    def test_only_mergeada_and_not_cwd_or_main(self) -> None:
        trees = [
            mod.Worktree("/repo/ai-harness", "aaa", "main"),
            mod.Worktree("/repo/worktrees/merged", "bbb", "feature/foo"),
            mod.Worktree("/repo/worktrees/open", "ccc", "feature/bar"),
            mod.Worktree("/repo/worktrees/current", "ddd", "feature/now"),
        ]
        rows = [
            mod.ActivityRow(
                repo="ai-harness",
                pasta="merged",
                kind="feature",
                slug="foo",
                branch="feature/foo",
                sha="bbb",
                pr_prod="https://example.com/1",
                merge_prod="sim",
                pr_develop="—",
                merge_develop="—",
                estado="mergeada",
            ),
            mod.ActivityRow(
                repo="ai-harness",
                pasta="open",
                kind="feature",
                slug="bar",
                branch="feature/bar",
                sha="ccc",
                pr_prod="https://example.com/2",
                merge_prod="não",
                pr_develop="—",
                merge_develop="—",
                estado="pr-aberta",
            ),
            mod.ActivityRow(
                repo="ai-harness",
                pasta="current",
                kind="feature",
                slug="now",
                branch="feature/now",
                sha="ddd",
                pr_prod="—",
                merge_prod="—",
                pr_develop="—",
                merge_develop="—",
                estado="aberta",
            ),
        ]
        got = mod.prune_candidates(
            trees,
            rows,
            cwd="/repo/worktrees/current/quality",
            main_path="/repo/ai-harness",
        )
        self.assertEqual([tree.path for tree in got], ["/repo/worktrees/merged"])


class SkillContractTest(unittest.TestCase):
    def test_skill_and_rule_document_the_flow(self) -> None:
        skill = Path(__file__).with_name("SKILL.md").read_text(encoding="utf-8")
        rule = Path(__file__).resolve().parents[2] / "rules" / "git-activity.md"
        rule_text = rule.read_text(encoding="utf-8")
        for needle in (
            "{YYYYMMDD}-{HHmm}-{kind}-{slug}",
            "{kind}/{YYYYMMDD}-{HHmm}-{slug}",
            "ATIVIDADES.md",
            "efêmera",
            "--prune",
        ):
            self.assertIn(needle, skill)
        self.assertIn("{YYYYMMDD}-{HHmm}-{kind}-{slug}", rule_text)
        self.assertIn("ATIVIDADES.md", rule_text)
        self.assertIn("--prune", rule_text)


if __name__ == "__main__":
    unittest.main()
