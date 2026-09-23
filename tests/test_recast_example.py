"""The copyable purchase example must never silently discard price or token."""
import importlib.util
from pathlib import Path
import sys
from unittest import TestCase
from unittest.mock import Mock, patch

EXAMPLES = Path(__file__).resolve().parents[1] / "examples" / "python"
sys.path.insert(0, str(EXAMPLES))
spec = importlib.util.spec_from_file_location("recast_quote", EXAMPLES / "recast_quote.py")
example = importlib.util.module_from_spec(spec)
spec.loader.exec_module(example)


class RecastExampleTests(TestCase):
    def setUp(self):
        self.client = Mock()
        self.creative = {"source_resource_id": "owned-id", "brief": "An original astronaut", "mode": "recast"}
        self.metadata = {"quote_token": "opaque-token", "quote_expires_at": 2000,
                         "quote": {"total_credits": 500}}
        self.saved = {"arguments": self.creative, "metadata": self.metadata}

    def test_quote_saves_exact_settings_without_purchase(self):
        self.client.call_tool.return_value = {"success": True, "metadata": self.metadata}
        saved = example.request_quote(self.client, self.creative, 600)
        self.assertEqual(saved["arguments"], self.creative)
        args = self.client.call_tool.call_args.args[1]
        self.assertTrue(args["estimate_only"])
        self.assertEqual(args["budget_cap_credits"], 600)
        self.assertNotIn("quote_token", args)

    def test_quote_refuses_missing_token_or_invalid_price(self):
        for metadata in ({"quote": {"total_credits": 500}},
                         {**self.metadata, "quote": {"total_credits": None}},
                         {**self.metadata, "quote": {"total_credits": True}},
                         {**self.metadata, "quote": {"total_credits": -1}}):
            with self.subTest(metadata=metadata):
                self.client.call_tool.return_value = {"metadata": metadata}
                with self.assertRaises(ValueError):
                    example.request_quote(self.client, self.creative, 600)

    def test_quote_refuses_server_price_above_requested_cap(self):
        self.client.call_tool.return_value = {"success": True, "metadata": self.metadata}
        with self.assertRaisesRegex(ValueError, "above"):
            example.request_quote(self.client, self.creative, 499)

    @patch.object(example.time, "time", return_value=1000)
    def test_purchase_and_retry_keep_same_token_and_ceiling(self, _clock):
        self.client.call_tool.return_value = {"success": True, "resource_id": "parent-id"}
        for _ in range(2):
            example.purchase_quote(self.client, self.saved, cap=900)
        first, second = self.client.call_tool.call_args_list
        self.assertEqual(first, second)
        args = first.args[1]
        self.assertEqual(args["budget_cap_credits"], 500)
        self.assertEqual(args["quote_token"], "opaque-token")
        self.assertFalse(args["estimate_only"])
        self.assertEqual(args["brief"], self.creative["brief"])

    @patch.object(example.time, "time", return_value=2000)
    def test_expired_quote_does_not_call_server(self, _clock):
        with self.assertRaisesRegex(ValueError, "expired"):
            example.purchase_quote(self.client, self.saved)
        self.client.call_tool.assert_not_called()

    @patch.object(example.time, "time", return_value=1000)
    def test_lower_budget_does_not_call_server(self, _clock):
        with self.assertRaisesRegex(ValueError, "above"):
            example.purchase_quote(self.client, self.saved, cap=499)
        self.client.call_tool.assert_not_called()

    @patch.object(example.time, "time", return_value=1000)
    def test_busy_error_does_not_trigger_fresh_quote_or_retry(self, _clock):
        self.client.call_tool.return_value = {"success": False, "error_code": "QUOTE_BUSY", "error": "Retry shortly"}
        with self.assertRaisesRegex(RuntimeError, "QUOTE_BUSY"):
            example.purchase_quote(self.client, self.saved)
        self.client.call_tool.assert_called_once()

    @patch.object(example.time, "time", return_value=1000)
    def test_failed_replay_preserves_parent_id_in_error(self, _clock):
        self.client.call_tool.return_value = {"success": False, "resource_id": "failed-parent", "error": "Run failed"}
        with self.assertRaisesRegex(RuntimeError, "existing job: failed-parent"):
            example.purchase_quote(self.client, self.saved)

    def test_status_only_reads_requested_parent(self):
        self.client.call_tool.return_value = {"success": True, "items": []}
        example.resource_status(self.client, "parent-id")
        self.client.call_tool.assert_called_once_with("lib_list", {
            "entity_type": "resources", "resource_ids": ["parent-id"],
        })
