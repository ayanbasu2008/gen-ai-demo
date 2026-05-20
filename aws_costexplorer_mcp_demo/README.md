# AWS Cost Explorer MCP Demo

This project demonstrates how to integrate an MCP (Model Context Protocol) server
with AWS Cost Explorer and a simple chat application.

## Features
- MCP server exposes AWS Cost Explorer tools (`get_services_cost`).
- Chat app routes user queries to MCP server.
- Summarizer agent extracts costs for Amazon EKS and ECS.
- Modular structure for easy extension.

## Project Structure
aws_costexplorer_mcp_demo/
├── mcp_server/          # MCP server exposing AWS Cost Explorer
├── chat_app/            # Chat app with router + summarizer
├── requirements.txt     # Dependencies
└── README.md            # Documentation



## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt

2. Set AWS credentials as environment variables:
export AWS_ACCESS_KEY_ID="your_access_key"
export AWS_SECRET_ACCESS_KEY="your_secret_key"
export AWS_REGION="us-east-1"

3. Run the MCP server:
python mcp_server/server.py

4. Run the chat app:
python chat_app/main.py

## Example Output

=== Chat App Answer ===

Amazon Elastic Kubernetes Service cost: 123.45 USD
Amazon Elastic Container Service cost: 98.76 USD

## Extending
Add more MCP tools (e.g., get_forecast, get_cost_and_usage).

Add more agents in chat_app for richer analysis.