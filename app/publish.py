"""Optional mirror of the built guide to Cloudflare R2 (or any S3-compatible bucket).

Configured by env only, so bucket credentials never pass through the web UI.
The mirror is a plain public bucket URL: access keys do not apply to it.
"""
import os

ENDPOINT = os.environ.get("R2_ENDPOINT")  # https://<account-id>.r2.cloudflarestorage.com
BUCKET = os.environ.get("R2_BUCKET")
PUBLIC_URL = os.environ.get("R2_PUBLIC_URL", "").rstrip("/")  # https://pub-xxxx.r2.dev or a custom domain


def enabled():
    return bool(ENDPOINT and BUCKET)


def upload(path):
    import boto3  # imported here so the app runs without it when R2 is not configured
    from botocore.config import Config

    s3 = boto3.client(
        "s3",
        endpoint_url=ENDPOINT,
        region_name="auto",
        aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],
        # R2 rejects the checksum trailers newer botocore sends by default
        config=Config(request_checksum_calculation="when_required", response_checksum_validation="when_required"),
    )
    # Same bytes under both names; the .xml object is served gzip-encoded.
    s3.upload_file(str(path), BUCKET, "epg.xml.gz", ExtraArgs={"ContentType": "application/x-gzip"})
    s3.upload_file(
        str(path), BUCKET, "epg.xml", ExtraArgs={"ContentType": "application/xml", "ContentEncoding": "gzip"}
    )
