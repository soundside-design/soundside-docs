import importlib.util
import json
from pathlib import Path
from unittest import TestCase

ROOT = Path(__file__).resolve().parents[1]


class PublicContractTests(TestCase):
    @staticmethod
    def _validator_module():
        spec = importlib.util.spec_from_file_location("validator", ROOT / "scripts/validate_public_contract.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_validator_accepts_current_tree(self):
        module = self._validator_module()
        self.assertEqual(module.main(), 0)

    def test_exact_sets_are_independent(self):
        contract = json.loads((ROOT / "_data/public-mcp-contract.json").read_text())
        sets = contract["sets"]
        self.assertEqual(len(sets["pro_tools"]), 19)
        self.assertEqual(sets["free_tools"], ["lib_list"])
        self.assertEqual(sets["authenticated_credit_only_tools"], ["compose_video"])
        self.assertEqual(len(sets["x402_eligible_tools"]), 17)

    def test_cast_visual_description_is_explicit_caller_authored(self):
        module = self._validator_module()
        contract = json.loads((ROOT / "_data/public-mcp-contract.json").read_text())
        compose = next(tool for tool in contract["tools"] if tool["name"] == "compose_video")
        module.validate_cast_visual_description_semantics(compose["inputSchema"])

        visual = module.cast_visual_description_schema(compose["inputSchema"])
        visual["description"] = (
            "Optional caller-authored appearance text for this explicit-cast member, "
            "used only by deterministic explicit-cast reference prompting. "
            "Auto-populated from entity discovery."
        )
        with self.assertRaisesRegex(AssertionError, "unavailable inference claim"):
            module.validate_cast_visual_description_semantics(compose["inputSchema"])
