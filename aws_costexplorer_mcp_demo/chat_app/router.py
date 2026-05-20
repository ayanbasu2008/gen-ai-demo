import datetime
import os
import sys

try:
    from dotenv import load_dotenv  
except ImportError:
    load_dotenv = None

# Support running as `python chat_app/main.py` by ensuring project root is importable.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

if load_dotenv is not None:
    load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

try:
    from mcp.client import Client  # Older MCP Python SDK API
except ImportError:
    Client = None

try:
    from mcp_server.aws_client import AWSCostExplorerClient
except ModuleNotFoundError:
    AWSCostExplorerClient = None

try:
    from chat_app.summarizer_agent import SummarizerAgent
except ModuleNotFoundError:
    from summarizer_agent import SummarizerAgent

def get_mock_response():
    # This is a simplified mock response for demonstration purposes.
    return {
        "ResultsByTime": [
            {
                "TimePeriod": {"Start": "2026-04-01", "End": "2026-04-30"},
                "Total": {
                    "BlendedCost": {"Amount": "200.00", "Unit": "USD"}
                },
                "Groups": [
                    {
                        "Keys": ["Amazon Elastic Container Service"],
                        "Metrics": {
                            "BlendedCost": {"Amount": "90.00", "Unit": "USD"}
                        }
                    },
                    {
                        "Keys": ["Amazon Elastic Kubernetes Service"],
                        "Metrics": {
                            "BlendedCost": {"Amount": "60.00", "Unit": "USD"}
                        }
                    },
                    {
                        "Keys": ["AWS Data Transfer"],
                        "Metrics": {
                            "BlendedCost": {"Amount": "30.00", "Unit": "USD"}
                        }
                    },
                    {
                        "Keys": ["Amazon Elastic Compute Cloud - Compute"],
                        "Metrics": {
                            "BlendedCost": {"Amount": "20.00", "Unit": "USD"}
                        }
                    },
                ]
            }
        ]
    }

def handle_query(query: str):
    # Detect AWS pricing intent
    if "price" in query.lower() or "cost" in query.lower():
        # Current month range
        today = datetime.date.today()
        start_date = today.replace(day=1).strftime("%Y-%m-%d")
        end_date = today.strftime("%Y-%m-%d")

        try:
            if Client is not None:
                client = Client("aws-costexplorer")
                response = client.call("get_services_cost", start_date=start_date, end_date=end_date)
            elif AWSCostExplorerClient is not None:
                client = AWSCostExplorerClient.from_env()
                # response = client.get_services_cost(start_date=start_date, end_date=end_date)
                response = get_mock_response()
            else:
                return "MCP client is unavailable and AWS client fallback could not be imported."
        except Exception as exc:
            error_text = str(exc)
            if "UnrecognizedClientException" in error_text or "security token included in the request is invalid" in error_text.lower():
                return (
                    "Unable to fetch AWS Cost Explorer data: AWS credentials/session token are invalid or expired. "
                    "If you use temporary credentials, set AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, and AWS_SESSION_TOKEN together. "
                    "If you use long-term credentials, remove any stale AWS_SESSION_TOKEN and retry."
                )
            return f"Unable to fetch AWS Cost Explorer data: {exc}"

        print("AWS Cost Explorer data = \n", response)
        # Summarize results
        try:
            summarizer = SummarizerAgent()
            return summarizer.run(response, [
                "Amazon Elastic Container Service",
                "Amazon Elastic Kubernetes Service",
                "AWS Data Transfer",
                "Amazon Elastic Compute Cloud - Compute",
                ])
        except Exception as exc:
            return f"Cost data retrieved, but summarization failed: {exc}"

    return "I can only answer AWS pricing queries in this demo."
