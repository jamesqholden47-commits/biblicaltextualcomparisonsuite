import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SUITE_ROOT = os.path.dirname(HERE)
if SUITE_ROOT not in sys.path:
    sys.path.insert(0, SUITE_ROOT)

from fastapi.testclient import TestClient
from app import app
from modules import audit_matrix_core as core


class TestAuditMatrixCore(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_sentence_tokenization(self):
        """Verify sentence splitting protects scriptural citations, abbreviations, and Hebrew."""
        text = (
            "# Heading Should Be Ignored\n"
            "In AD 110, Ignatius of Antioch wrote his letters. "
            "Deuteronomy 17:8-12 established a supreme court of final appeal. "
            "Exodus 20:4-5 distinguishes between a pesel and civil bowing."
        )
        sentences = core.tokenize_sentences(text)
        self.assertEqual(len(sentences), 3)
        self.assertIn("ignatius of antioch", sentences[0][0])
        self.assertIn("deuteronomy 17 8 12", sentences[1][0])
        self.assertIn("exodus 20 4 5", sentences[2][0])

    def test_rule_11_lossless_pass(self):
        """Verify Rule 11 passes when all substantive source sentences survive in target."""
        source = (
            "Deuteronomy 17:8-12 proves the Old Covenant had a supreme court of appeal.\n"
            "In Matthew 16:18-19, Jesus transferred the Davidic keys to Simon Peter.\n"
            "The St. Thomas Christians of Malabar preserved the Eucharistic sacrifice in isolation."
        )
        target = (
            "# Consolidated Chapter\n\n"
            "Deuteronomy 17:8-12 proves the Old Covenant had a supreme court of appeal.\n"
            "Furthermore, in Matthew 16:18-19, Jesus transferred the Davidic keys to Simon Peter.\n"
            "As demonstrated in our empirical analysis, the St. Thomas Christians of Malabar preserved the Eucharistic sacrifice in isolation."
        )
        res = core.compute_audit_matrix(source, target)
        sum_data = res["summary"]

        self.assertTrue(sum_data["rule_11_passed"])
        self.assertEqual(sum_data["omitted_count"], 0)
        self.assertEqual(sum_data["preserved_count"], 3)
        self.assertEqual(sum_data["preservation_rate"], 100.0)
        self.assertEqual(len(res["omitted_sentences"]), 0)
        self.assertIn("LOSSLESS", sum_data["verdict"])

    def test_rule_11_falsification_loss_detected(self):
        """Falsification test: Dropping even a single substantive sentence MUST trigger FAIL."""
        source = (
            "Deuteronomy 17:8-12 proves the Old Covenant had a supreme court of appeal.\n"
            "In Matthew 16:18-19, Jesus transferred the Davidic keys to Simon Peter.\n"
            "The St. Thomas Christians of Malabar preserved the Eucharistic sacrifice in isolation."
        )
        # Dropped the St. Thomas Christians sentence:
        target = (
            "# Summarized Draft (Defective)\n\n"
            "Deuteronomy 17:8-12 proves the Old Covenant had a supreme court of appeal.\n"
            "In Matthew 16:18-19, Jesus transferred the Davidic keys to Simon Peter."
        )
        res = core.compute_audit_matrix(source, target)
        sum_data = res["summary"]

        self.assertFalse(sum_data["rule_11_passed"])
        self.assertEqual(sum_data["omitted_count"], 1)
        self.assertEqual(sum_data["preserved_count"], 2)
        self.assertLess(sum_data["preservation_rate"], 100.0)
        self.assertEqual(len(res["omitted_sentences"]), 1)
        self.assertIn("malabar", res["omitted_sentences"][0]["norm"])
        self.assertIn("RULE 11 DEFECT", sum_data["verdict"])

    def test_rule_11_near_match_tolerance(self):
        """Verify token Jaccard near-match survives minor grammatical rewording."""
        source = "The St. Thomas Christians of Kerala, India preserved the ancient Eucharistic sacrifice for fifteen centuries in complete isolation."
        target = "In complete isolation, the St. Thomas Christians of Kerala, India preserved the ancient Eucharistic sacrifice for fifteen centuries."
        
        res = core.compute_audit_matrix(source, target)
        self.assertTrue(res["summary"]["rule_11_passed"])
        self.assertEqual(res["summary"]["omitted_count"], 0)

    def test_rule_13_infrastructure_classifier(self):
        """Verify Rule 13 catches infrastructure files and keywords."""
        infra_path = "06_SOURCE_MATERIAL/_SESSION_TRANSCRIPTS/transcript_2026.md"
        is_infra, reason = core.check_rule_13_infrastructure(infra_path)
        self.assertTrue(is_infra)
        self.assertIn("_SESSION_TRANSCRIPTS", reason)

        ostep_text = "According to OSTEP (Operating Systems: Three Easy Pieces), disk caching improves throughput."
        is_infra_text, reason_text = core.check_rule_13_infrastructure(ostep_text)
        self.assertTrue(is_infra_text)
        self.assertIn("OSTEP", reason_text)

        valid_text = "St. Irenaeus of Lyons in Adversus Haereses 3.3.2 testifies to Roman primacy."
        is_infra_valid, _ = core.check_rule_13_infrastructure(valid_text)
        self.assertFalse(is_infra_valid)

    def test_campaign_registry(self):
        """Verify all 8 laser deduplication campaigns are registered, totaling 730 clusters."""
        campaigns = core.list_campaigns()
        self.assertEqual(len(campaigns), 8)
        
        total_clusters = sum(c["cluster_count"] for c in campaigns)
        self.assertEqual(total_clusters, 730)
        
        camp_ids = [c["id"] for c in campaigns]
        expected_ids = [f"CAMP-0{i}" for i in range(1, 9)]
        self.assertEqual(camp_ids, expected_ids)

    def test_html_matrix_rendering(self):
        """Verify HTML matrix renders table, badges, and statistics."""
        source = (
            "Deuteronomy 17:8-12 proves the Old Covenant had a supreme court of appeal.\n"
            "The Council of Nicaea II in 787 AD dogmatically defended the veneration of sacred icons against iconoclasm."
        )
        target = "Deuteronomy 17:8-12 proves the Old Covenant had a supreme court of appeal."
        res = core.compute_audit_matrix(source, target)
        html = core.render_html_diff_matrix(res, title="Unit Test Matrix")
        
        self.assertIn("<!DOCTYPE html>", html)
        self.assertIn("FAIL (SENTENCE LOSS DETECTED)", html)
        self.assertIn("OMITTED", html)
        self.assertIn("Unit Test Matrix", html)

    def test_api_endpoints(self):
        """Verify FastAPI HTTP endpoints for audit module."""
        # 1. Campaigns
        resp_camp = self.client.get("/api/audit/campaigns")
        self.assertEqual(resp_camp.status_code, 200)
        data_camp = resp_camp.json()
        self.assertEqual(data_camp["count"], 8)

        # 2. Matrix calculation (JSON)
        payload = {
            "source_text": "Sentence A in source note. Sentence B in source note.",
            "target_text": "Sentence A in source note. Sentence B in source note. Extra target sentence.",
        }
        resp_matrix = self.client.post("/api/audit/matrix", json=payload)
        self.assertEqual(resp_matrix.status_code, 200)
        data_matrix = resp_matrix.json()
        self.assertTrue(data_matrix["summary"]["rule_11_passed"])
        self.assertEqual(data_matrix["summary"]["omitted_count"], 0)

        # 3. HTML diff matrix
        resp_html = self.client.post("/api/audit/matrix/html", json=payload)
        self.assertEqual(resp_html.status_code, 200)
        self.assertIn("text/html", resp_html.headers["content-type"])
        self.assertIn("PASS (LOSSLESS)", resp_html.text)

        # 4. Fast loss verifier
        resp_verify = self.client.post("/api/audit/verify_loss", json=payload)
        self.assertEqual(resp_verify.status_code, 200)
        data_verify = resp_verify.json()
        self.assertTrue(data_verify["rule_11_passed"])
        self.assertEqual(data_verify["omitted_count"], 0)


if __name__ == "__main__":
    unittest.main()
