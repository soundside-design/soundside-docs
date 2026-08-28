from unittest import TestCase
from unittest.mock import patch

from soundside import Soundside
from soundside.types import ToolResult


class ClientContractTests(TestCase):
    def setUp(self):
        self.client = Soundside("test")

    def test_artifact_uses_server_type_and_type_specific_fields(self):
        with patch.object(self.client, "call_tool", return_value=ToolResult(success=True, data={"resource_id": "r", "status": "completed"})) as call, patch.object(self.client, "_ensure_url", side_effect=lambda resource: resource):
            self.client.create_artifact("chart", chart_type="bar", data={"labels": [], "datasets": []})
        args = call.call_args.args[1]
        self.assertEqual(args["type"], "chart")
        self.assertEqual(args["chart_type"], "bar")
        self.assertNotIn("artifact_type", args)
        self.assertNotIn("content", args)

    def test_transcribe_is_prompt_free_and_canonical(self):
        with patch.object(self.client, "call_tool", return_value=ToolResult(success=True, data={})) as call:
            self.client.transcribe("resource", subtitle_formats=["srt", "vtt"])
        name, args = call.call_args.args
        self.assertEqual(name, "analyze_media")
        self.assertEqual(args["analysis_type"], "transcribe")
        self.assertEqual(args["resource_id"], "resource")
        self.assertNotIn("prompt", args)
        self.assertNotIn("provider", args)
        self.assertEqual(args["subtitle_formats"], ["srt", "vtt"])
