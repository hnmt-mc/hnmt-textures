import json
import hashlib
import unittest
import uuid

import make_manifest


class ManifestTests(unittest.TestCase):
    def test_the_manifest_points_at_the_release_asset_and_carries_the_sha1(self):
        data = b"zip bytes"
        result = make_manifest.manifest("v0.1.0", data)
        self.assertEqual(result["version"], "v0.1.0")
        self.assertEqual(result["url"], "https://github.com/hnmt-mc/hnmt-textures/releases/download/v0.1.0/hnmt-textures.zip")
        self.assertEqual(result["sha1"], hashlib.sha1(data).hexdigest())
        self.assertEqual(set(result), {"version", "url", "sha1", "id", "capabilities"})
        json.dumps(result)

    def test_the_id_follows_the_content_so_a_change_makes_clients_download_again(self):
        a = make_manifest.manifest("v0.1.0", b"one")
        b = make_manifest.manifest("v0.1.1", b"two")
        c = make_manifest.manifest("v0.1.2", b"one")
        self.assertNotEqual(a["id"], b["id"])
        self.assertEqual(a["id"], c["id"], "同じ中身なら、同じID")
        uuid.UUID(a["id"])

    def test_a_tag_that_is_not_a_version_is_refused(self):
        for tag in ("0.1.0", "v1", "main", "v1.2.3-beta", ""):
            with self.assertRaises(ValueError, msg=tag):
                make_manifest.manifest(tag, b"x")


if __name__ == "__main__":
    unittest.main()
