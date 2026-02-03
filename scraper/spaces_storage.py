# spaces_storage.py
import os
import boto3

def _env_bool(name: str, default="0") -> bool:
    return os.getenv(name, default).lower() in ("1", "true", "yes", "y")

class SpacesStorage:
    def __init__(self):
        self.bucket = os.environ["SPACES_BUCKET"]
        self.region = os.getenv("SPACES_REGION", "sfo3")
        self.endpoint = os.getenv("SPACES_ENDPOINT", "https://sfo3.digitaloceanspaces.com")
        self.prefix = os.getenv("SPACES_PREFIX", "").strip("/")

        self.s3 = boto3.client(
            "s3",
            region_name=self.region,
            endpoint_url=self.endpoint,
        )

    def key(self, k: str) -> str:
        k = k.lstrip("/")
        return f"{self.prefix}/{k}" if self.prefix else k

    def put_bytes(self, key: str, data: bytes, content_type: str = "application/octet-stream"):
        k = self.key(key)
        self.s3.put_object(
            Bucket=self.bucket,
            Key=k,
            Body=data,
            ContentType=content_type,
        )
        return k
