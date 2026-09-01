#!/usr/bin/env python3
"""sql-guard: só cliente de banco; commit message e WHERE verdadeiro passam."""

from __future__ import annotations

import unittest

import sql_guard

CASES = {
    "drop psql": ('psql -c "DROP TABLE t"', "deny"),
    "delete no where": ('psql -c "DELETE FROM t"', "deny"),
    "delete where": ('psql -c "DELETE FROM t WHERE id = 1"', "allow"),
    "truncate": ('mysql -e "TRUNCATE t"', "deny"),
    "commit msg": ('git commit -m "DELETE unused WHERE leftover"', "allow"),
    "echo drop": ('echo "DROP TABLE t"', "allow"),
    "file sql": ("psql -f migrations/drop.sql", "allow"),
    "docker exec": ('docker exec db psql -c "DROP DATABASE app"', "deny"),
}


class SqlGuardTest(unittest.TestCase):
    def test_cases(self) -> None:
        for name, (command, want) in CASES.items():
            with self.subTest(name):
                got = sql_guard.decide(
                    {
                        "toolName": "run_terminal_command",
                        "toolInput": {"command": command},
                    }
                )["decision"]
                self.assertEqual(got, want)


if __name__ == "__main__":
    unittest.main()
