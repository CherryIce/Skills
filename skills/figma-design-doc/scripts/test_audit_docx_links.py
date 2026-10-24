"""Behavior tests for DOCX links. Fixtures are temporary and never touch source files."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from xml.sax.saxutils import escape, quoteattr
from zipfile import ZipFile

SCRIPT = Path(__file__).with_name("audit_docx_links.py")
SPEC = importlib.util.spec_from_file_location("audit_docx_links", SCRIPT)
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)
NS = ('xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
      'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"')
A = "https://www.figma.com/design/Demo/Design?node-id=10-20"
B = "https://www.figma.com/design/Demo/Design?node-id=10-21"
C = "https://www.figma.com/design/Demo/Design?node-id=10-22"


def text(s):
    return "<w:r><w:t>" + escape(s) + "</w:t></w:r>"


def link(rid, label):
    return '<w:hyperlink r:id="' + rid + '">' + text(label) + '</w:hyperlink>'


def simple(url, label):
    return '<w:fldSimple w:instr=' + quoteattr(' HYPERLINK "' + url + '" ') + '>' + text(label) + '</w:fldSimple>'


def complex_field(url, label):
    instruction = ' HYPERLINK "' + url + '" '
    chunks = [instruction[:6], instruction[6:22], instruction[22:]]
    return ('<w:r><w:fldChar w:fldCharType="begin"/></w:r>' +
            ''.join('<w:r><w:instrText>' + escape(s) + '</w:instrText></w:r>' for s in chunks) +
            '<w:r><w:fldChar w:fldCharType="separate"/></w:r>' + text(label[:2]) + text(label[2:]) +
            '<w:r><w:fldChar w:fldCharType="end"/></w:r>')


def rel_xml(rows):
    return ('<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">' +
            ''.join('<Relationship Id=' + quoteattr(rid) + ' Target=' + quoteattr(url) +
                    ' Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink" TargetMode="External"/>'
                    for rid, url in rows) + '</Relationships>')


def inventory(*ids, **changes):
    rows = []
    for node in ids:
        row = dict(file_key="Demo", node_id=node, role="page", group=node,
                   version="中文亮色", scope_node_id="1:2", verified=True, exists=True, visible=True)
        row.update(changes)
        rows.append(row)
    return dict(scopes=[dict(file_key="Demo", node_id="1:2")], targets=rows)


class AuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="figma_doc_audit_test_")
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def doc(self, name, body, rels=(), extra=None):
        p = self.root / name
        with ZipFile(p, "w") as z:
            z.writestr("word/document.xml", '<w:document ' + NS + '><w:body>' + body + '</w:body></w:document>')
            z.writestr("word/_rels/document.xml.rels", rel_xml(rels))
            for part, contents in (extra or {}).items():
                z.writestr(part, contents)
        return p

    def test_relationship_and_context(self):
        p = self.doc("a.docx", '<w:p>' + text("搜索 无结果") + '</w:p><w:p>' + link("r1", "中文亮色") + '</w:p>', [("r1", A)])
        report = M.audit(p, inventory("10:20"))
        self.assertTrue(report["local_checks_passed"])
        self.assertEqual(report["links"][0]["context"], "搜索 无结果")
        self.assertFalse(report["live_figma_access_performed"])

    def test_simple_and_split_complex_field(self):
        p = self.doc("a.docx", '<w:p>' + simple(A, "中文亮色") + complex_field(B, "中文暗色") + '</w:p>')
        rows = M.extract_docx(p)["links"]
        self.assertEqual([(r["node_id"], r["label"]) for r in rows], [("10:20", "中文亮色"), ("10:21", "中文暗色")])

    def test_word_resave_preserves_link_meaning(self):
        a = self.doc("before.docx", '<w:p>' + link("r1", "中文亮色") + '</w:p>', [("r1", A)])
        b = self.doc("after.docx", '<w:p>' + complex_field(A, "中文亮色") + '</w:p>')
        self.assertTrue(M.audit(b, preserve_from=a)["preservation_check"]["preserved"])

    def test_tables_headers_and_footnotes(self):
        extra = {"word/header1.xml": '<w:hdr ' + NS + '><w:p>' + simple(B, "Header") + '</w:p></w:hdr>',
                 "word/footnotes.xml": '<w:footnotes ' + NS + '><w:footnote><w:p>' + complex_field(C, "Footnote") + '</w:p></w:footnote></w:footnotes>'}
        p = self.doc("a.docx", '<w:tbl><w:tr><w:tc><w:p>' + simple(A, "Cell") + '</w:p></w:tc></w:tr></w:tbl>', extra=extra)
        self.assertEqual(M.audit(p)["clickable_figma_links"], 3)

    def test_deleted_links_are_not_covered(self):
        p = self.doc("a.docx", '<w:p><w:del>' + link("r1", "old") + '</w:del></w:p>', [("r1", A)])
        self.assertEqual(M.audit(p)["clickable_figma_links"], 0)

    def test_missing_relationship_fails(self):
        p = self.doc("a.docx", '<w:p>' + link("missing", "bad") + '</w:p>')
        self.assertFalse(M.audit(p)["local_checks_passed"])

    def test_plain_concatenated_urls_are_not_clickable(self):
        p = self.doc("a.docx", '<w:p>' + text(A + B) + '</w:p>')
        report = M.audit(p, inventory("10:20", "10:21"))
        self.assertEqual(report["clickable_figma_links"], 0)
        self.assertEqual(len(report["plain_text_urls"]), 2)
        self.assertEqual(len(report["inventory_check"]["missing_targets"]), 2)

    def test_concatenated_hyperlink_target_fails(self):
        p = self.doc("a.docx", '<w:p>' + link("r1", "bad") + '</w:p>', [("r1", A + B)])
        self.assertFalse(M.audit(p)["local_checks_passed"])

    def test_visible_url_pointing_elsewhere_fails(self):
        p = self.doc("a.docx", '<w:p>' + link("r1", A) + '</w:p>', [("r1", B)])
        self.assertFalse(M.audit(p)["local_checks_passed"])

    def test_missing_and_unexpected_targets(self):
        p = self.doc("a.docx", '<w:p>' + simple(A, "one") + simple(B, "two") + '</w:p>')
        c = M.audit(p, inventory("10:20", "10:22"))["inventory_check"]
        self.assertEqual(c["missing_targets"], [["Demo", "10:22"]])
        self.assertEqual(c["unexpected_targets"], [["Demo", "10:21"]])

    def test_unverified_evidence_and_wrong_scope_fail(self):
        p = self.doc("a.docx", '<w:p>' + simple(A, "one") + '</w:p>')
        for changes in [dict(verified=False), dict(exists=False), dict(scope_node_id="9:9")]:
            self.assertFalse(M.audit(p, inventory("10:20", **changes))["local_checks_passed"])

    def test_explicit_hidden_component_state(self):
        p = self.doc("a.docx", '<w:p>' + simple(A, "hidden variant") + '</w:p>')
        self.assertFalse(M.audit(p, inventory("10:20", visible=False))["local_checks_passed"])
        report = M.audit(p, inventory("10:20", visible=False, hidden_state_reason="用户要求盘点的组件变体"))
        self.assertTrue(report["local_checks_passed"])
        self.assertEqual(len(report["inventory_check"]["intentional_hidden_states"]), 1)

    def test_branch_and_hostname_normalization(self):
        self.assertEqual(M.figma_target("https://www.figma.com/design/Main/branch/Branch/Name?node-id=10%3A20&t=expiring"), ("Branch", "10:20"))
        self.assertIsNone(M.figma_target("https://notfigma.com/design/Demo/Name?node-id=10-20"))

    def test_intentional_repeat_is_reported_not_rejected(self):
        p = self.doc("a.docx", '<w:p>' + simple(A, "entry") + simple(A, "detail") + '</w:p>')
        report = M.audit(p, inventory("10:20"))
        self.assertTrue(report["local_checks_passed"])
        self.assertEqual(report["clickable_figma_links"], 2)
        self.assertEqual(report["unique_figma_targets"], 1)
        self.assertEqual(report["repeated_targets"][0]["occurrences"], 2)

    def test_preservation_allows_additions_but_not_reorder(self):
        def rows(values):return [{"url": u, "label": u} for u in values]
        self.assertTrue(M.preservation_check(rows([A, B]), rows([C, A, C, B]))["preserved"])
        self.assertFalse(M.preservation_check(rows([A, B]), rows([B, A]))["preserved"])

    def test_unterminated_field_fails(self):
        p = self.doc("a.docx", '<w:p><w:r><w:fldChar w:fldCharType="begin"/></w:r></w:p>')
        self.assertFalse(M.audit(p)["local_checks_passed"])

    def test_nested_textbox_not_double_counted(self):
        p = self.doc("a.docx", '<w:p><w:r><w:drawing><w:txbxContent><w:p>' + simple(A, A) + '</w:p></w:txbxContent></w:drawing></w:r></w:p>')
        report = M.audit(p)
        self.assertEqual(report["clickable_figma_links"], 1)
        self.assertEqual(report["plain_text_urls"], [])

    def test_cli_cannot_overwrite_document_with_json(self):
        p = self.doc("a.docx", '<w:p>' + simple(A, "one") + '</w:p>')
        old = p.read_bytes()
        done = subprocess.run([sys.executable, "-B", str(SCRIPT), str(p), "--json", str(p)], capture_output=True)
        self.assertEqual(done.returncode, 2)
        self.assertEqual(old, p.read_bytes())


if __name__ == "__main__":
    unittest.main()
