"""Check the trust declarations used by the Mac package manifest."""

from pathlib import Path
import unittest


class BrewfileTests(unittest.TestCase):
    def test_third_party_taps_are_explicitly_trusted(self):
        manifest = Path(__file__).resolve().parents[1] / "Brewfile"
        taps = [
            line
            for line in manifest.read_text().splitlines()
            if line.startswith("tap ")
        ]
        self.assertEqual(
            taps,
            [
                'tap "buildkite/buildkite", trusted: true',
                'tap "hashicorp/tap", trusted: true',
            ],
        )


if __name__ == "__main__":
    unittest.main()
