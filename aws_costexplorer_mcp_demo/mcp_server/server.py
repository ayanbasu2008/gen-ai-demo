from mcp.server.fastmcp import FastMCP
from aws_client import AWSCostExplorerClient

client = AWSCostExplorerClient.from_env()
server = FastMCP("aws-costexplorer")

@server.tool("get_services_cost")
def get_services_cost(start_date: str, end_date: str):
    """Break down AWS costs by service."""
    return client.get_services_cost(start_date, end_date)

if __name__ == "__main__":
    server.run()
