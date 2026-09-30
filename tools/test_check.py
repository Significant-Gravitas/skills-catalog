"""The roster check refuses text that makes an expert wait for its owner's yes."""

import unittest

import check


class ApprovalWaitTests(unittest.TestCase):
    def errors(self, **fields):
        data = {"key": "alex", "name": "Alex", "skills": [], **fields}
        found: list[str] = []
        check._check_expert("experts/alex.yml", "alex", data, set(), found)
        return [e for e in found if check.APPROVAL_WAIT_HINT in e]

    def test_a_wait_for_the_owner_is_refused_wherever_it_sits(self):
        cases = {
            "boundaries": "Nothing sends without the owner's yes to that specific action.",
            "bio": "I draft it, name what I'm asking for, and wait.",
            "identity": "Each routine stays off until they say yes.",
            "day_one": [{"title": "Replies", "description": "Stops at your yes.", "timing": "Day 1"}],
            "routines": [{"key": "r", "title": "R", "prompt": "Every diff waits for the owner's yes.",
                          "crons": [], "asks": [], "session_mode": "FRESH"}],
            "voice_samples": [{"label": "Handoff", "text": "Say yes and I will file the stories."}],
        }
        for field, value in cases.items():
            with self.subTest(field=field):
                self.assertEqual(len(self.errors(**{field: value})), 1)

    def test_who_decides_and_what_the_expert_does_are_allowed(self):
        allowed = (
            "Never commit the team to a date the decision maker has not approved. "
            "Never approve a discount outside the guardrail bands. "
            "Send only what the owner asked you to. "
            "The routines stay off until the owner switches them on. "
            "If the close is not done, say so and wait for the close-done flag."
        )
        self.assertEqual(self.errors(boundaries=allowed), [])


if __name__ == "__main__":
    unittest.main()
