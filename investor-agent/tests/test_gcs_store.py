import sys
import json
import types
import unittest
import unittest.mock


class _FakeBlob:
    def __init__(self, name):
        self.name = name
        self.uploaded_bytes = None
        self.content_type = None

    def upload_from_string(self, data, content_type=None):
        self.uploaded_bytes = data
        self.content_type = content_type


class _FakeBucket:
    def __init__(self):
        self.last_blob = None

    def blob(self, name):
        self.last_blob = _FakeBlob(name)
        return self.last_blob


class _FakeClient:
    def __init__(self):
        self.bucket_name = None
        self.bucket_obj = _FakeBucket()

    def bucket(self, name):
        self.bucket_name = name
        return self.bucket_obj


class _Config:
    def __init__(self, bucket_name="test-bucket", prefix="investor-analysis"):
        self.gcs_bucket_name = bucket_name
        self.gcs_prefix = prefix


class GCSStoreTests(unittest.TestCase):
    def test_store_json_uses_prefix_and_uploads_bytes(self):
        fake_client = _FakeClient()

        google = types.ModuleType("google")
        cloud = types.ModuleType("google.cloud")
        storage = types.ModuleType("google.cloud.storage")
        storage.Client = lambda: fake_client
        cloud.storage = storage
        google.cloud = cloud

        with unittest.mock.patch.dict(
            sys.modules,
            {
                "google": google,
                "google.cloud": cloud,
                "google.cloud.storage": storage,
            },
        ):
            from app.storage.gcs_store import GCSStore

            store = GCSStore(_Config())
            result = store.store_json({"ok": True}, "AAPL")

        self.assertTrue(result.startswith("gs://test-bucket/investor-analysis/AAPL/AAPL_analysis_"))
        self.assertTrue(result.endswith(".json"))
        self.assertIsNotNone(fake_client.bucket_obj.last_blob)
        self.assertEqual(fake_client.bucket_obj.last_blob.content_type, "application/json")
        payload = json.loads(fake_client.bucket_obj.last_blob.uploaded_bytes.decode("utf-8"))
        self.assertEqual(payload, {"ok": True})


if __name__ == "__main__":
    unittest.main()
