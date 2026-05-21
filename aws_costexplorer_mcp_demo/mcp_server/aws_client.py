import boto3
import json
import os
from datetime import date, datetime


def _serialize(value):
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    raise TypeError(f"Type {type(value)} not serializable")

class AWSCostExplorerClient:
    def __init__(
        self,
        aws_access_key,
        aws_secret_key,
        aws_region="us-east-1",
        aws_session_token=None,
        aws_profile=None,
    ):
        client_kwargs = {
            "service_name": "ce",
            "region_name": aws_region,
        }
        if aws_access_key and aws_secret_key:
            client_kwargs["aws_access_key_id"] = aws_access_key
            client_kwargs["aws_secret_access_key"] = aws_secret_key
            if aws_session_token:
                client_kwargs["aws_session_token"] = aws_session_token
            self.client = boto3.client(**client_kwargs)
        elif aws_profile:
            self.client = boto3.Session(profile_name=aws_profile, region_name=aws_region).client("ce")
        else:
            self.client = boto3.client(**client_kwargs)

    @classmethod
    def from_env(cls):
        aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
        aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        aws_session_token = os.getenv("AWS_SESSION_TOKEN")
        aws_region = os.getenv("AWS_REGION", "us-east-1")
        aws_profile = os.getenv("AWS_PROFILE")

        # Empty token values are common in env files and should be treated as missing.
        if aws_session_token is not None and not aws_session_token.strip():
            aws_session_token = None

        return cls(
            aws_access_key=aws_access_key,
            aws_secret_key=aws_secret_key,
            aws_region=aws_region,
            aws_session_token=aws_session_token,
            aws_profile=aws_profile,
        )

    def get_services_cost(self, start_date, end_date):
        response = self.client.get_cost_and_usage(
            TimePeriod={"Start": start_date, "End": end_date},
            Granularity="MONTHLY",
            Metrics=["UnblendedCost"],
            GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}]
        )
        response.pop("ResponseMetadata", None)
        print("Raw AWS Cost Explorer response:", response)
        return json.loads(json.dumps(response, default=_serialize))
