import datetime
import os
import sys
import anyio
import json

try:
    from dotenv import load_dotenv  
except ImportError:
    load_dotenv = None

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

if load_dotenv is not None:
    load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

try:
    from mcp.client.session import ClientSession
    from mcp.client.stdio import StdioServerParameters, stdio_client
except ImportError:
    ClientSession = None
    StdioServerParameters = None
    stdio_client = None

try:
    from chat_app.summarizer_agent import SummarizerAgent
except ModuleNotFoundError:
    from summarizer_agent import SummarizerAgent

async def _call_mcp_server_get_services_cost(start_date: str, end_date: str):
    if not all([ClientSession, StdioServerParameters, stdio_client]):
        raise RuntimeError("MCP Python SDK is unavailable in this environment.")

    server_script = os.path.join(PROJECT_ROOT, "mcp_server", "server.py")
    server_params = StdioServerParameters(
        command=sys.executable,
        args=[server_script],
        env=os.environ.copy(),
    )

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            result = await session.call_tool(
                "get_services_cost",
                {"start_date": start_date, "end_date": end_date},
            )

    if hasattr(result, "content") and result.content:
        first_content = result.content[0]
        if hasattr(first_content, "text"):
            return first_content.text
    return result

def handle_query(query: str):
    if "price" in query.lower() or "cost" in query.lower():
        today = datetime.date.today()
        start_date = today.replace(day=1).strftime("%Y-%m-%d")
        end_date = today.strftime("%Y-%m-%d")

        try:
            print("Execution path: chat_app -> mcp_server -> AWS Cost Explorer")
            response = anyio.run(_call_mcp_server_get_services_cost, start_date, end_date)
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

        if isinstance(response, str):
            try:
                response = json.loads(response)
            except Exception:
                pass

        print("Response path: AWS Cost Explorer -> mcp_server -> chat_app")

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
