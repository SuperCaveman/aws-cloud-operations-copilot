"""A fixed, S3-backed retrieval boundary for the sole Phase 1 runbook."""

from __future__ import annotations

from typing import Any


ORDERS_API_RUNBOOK_KEY = "runbooks/orders-api-missing-config.md"


class RunbookRetriever:
    """Read exactly one allow-listed runbook object and no caller-selected S3 key."""

    def __init__(self, bucket_name: str, s3_client: Any) -> None:
        if not bucket_name:
            raise ValueError("A non-empty runbook bucket name is required.")
        self.bucket_name = bucket_name
        self.s3_client = s3_client

    def get_orders_api_runbook(self) -> dict[str, str]:
        response = self.s3_client.get_object(
            Bucket=self.bucket_name,
            Key=ORDERS_API_RUNBOOK_KEY,
        )
        body = response["Body"].read().decode("utf-8")
        return {
            "source": f"s3://{self.bucket_name}/{ORDERS_API_RUNBOOK_KEY}",
            "content": body,
        }


def build_aws_runbook_retriever(bucket_name: str, region: str) -> RunbookRetriever:
    """Create the S3 client only at runtime, keeping unit tests fully offline."""
    import boto3

    return RunbookRetriever(
        bucket_name=bucket_name,
        s3_client=boto3.client("s3", region_name=region),
    )
