try:
    from chat_app.router import handle_query
except ModuleNotFoundError:
    from router import handle_query

if __name__ == "__main__":
    query = "What is the latest price of Amazon EKS and ECS"
    answer = handle_query(query)
    print("\n=== Chat App Answer ===\n")
    print(answer)
