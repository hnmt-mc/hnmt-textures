import hashlib
import json
import unittest

import make_bedrock_manifest


class BedrockManifestTests(unittest.TestCase):
    PACK = b"pack bytes"
    MAPPINGS = b'{"format_version": 2}'

    def make(self, tag="v0.1.0"):
        return make_bedrock_manifest.manifest(tag, self.PACK, self.MAPPINGS)

    def test_it_lists_the_pack_and_the_mappings_with_their_places(self):
        result = self.make()
        self.assertEqual(result["version"], "v0.1.0")
        files = {entry["name"]: entry for entry in result["files"]}
        self.assertEqual(set(files), {"hnmt-bedrock.mcpack", "hnmt.json"})
        self.assertEqual(files["hnmt-bedrock.mcpack"]["target"], "packs")
        self.assertEqual(files["hnmt.json"]["target"], "custom_mappings")

    def test_the_urls_point_at_the_release_assets(self):
        files = {entry["name"]: entry for entry in self.make("v1.2.3")["files"]}
        self.assertEqual(files["hnmt-bedrock.mcpack"]["url"],
                         "https://github.com/hnmt-mc/hnmt-textures/releases/download/v1.2.3/hnmt-bedrock.mcpack")
        self.assertEqual(files["hnmt.json"]["url"],
                         "https://github.com/hnmt-mc/hnmt-textures/releases/download/v1.2.3/hnmt.json")

    def test_each_file_carries_its_own_sha1(self):
        files = {entry["name"]: entry for entry in self.make()["files"]}
        self.assertEqual(files["hnmt-bedrock.mcpack"]["sha1"], hashlib.sha1(self.PACK).hexdigest())
        self.assertEqual(files["hnmt.json"]["sha1"], hashlib.sha1(self.MAPPINGS).hexdigest())

    def test_the_blocks_mapping_is_listed_when_given(self):
        blocks = b'{"format_version": 1}'
        result = make_bedrock_manifest.manifest("v0.1.0", self.PACK, self.MAPPINGS, blocks)
        files = {entry["name"]: entry for entry in result["files"]}
        self.assertEqual(set(files), {"hnmt-bedrock.mcpack", "hnmt.json", "hnmt_blocks.json"})
        self.assertEqual(files["hnmt_blocks.json"]["target"], "custom_mappings")
        self.assertEqual(files["hnmt_blocks.json"]["sha1"], hashlib.sha1(blocks).hexdigest())
        self.assertEqual(files["hnmt_blocks.json"]["url"],
                         "https://github.com/hnmt-mc/hnmt-textures/releases/download/v0.1.0/hnmt_blocks.json")

    def test_the_result_can_be_written_as_json(self):
        json.dumps(self.make())

    def test_a_tag_that_is_not_a_version_is_refused(self):
        for tag in ("0.1.0", "v1", "main", "v1.2.3-beta", ""):
            with self.assertRaises(ValueError, msg=tag):
                self.make(tag)


if __name__ == "__main__":
    unittest.main()
