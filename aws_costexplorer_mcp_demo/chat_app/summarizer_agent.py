import os
from openai import OpenAI

class SummarizerAgent:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=api_key)

    def _get_metric(self, metrics):
        # Prefer common Cost Explorer metrics, then fall back to the first available metric.
        preferred_keys = ["UnblendedCost", "BlendedCost", "AmortizedCost", "NetUnblendedCost"]
        for key in preferred_keys:
            if key in metrics:
                return metrics[key]

        for value in metrics.values():
            if isinstance(value, dict) and "Amount" in value and "Unit" in value:
                return value

        return None

    def run(self, response, services):
        results_by_time = response.get("ResultsByTime", [])
        if not results_by_time:
            return "No AWS cost data was returned for the selected period."

        results = results_by_time[0].get("Groups", [])

        # Extract raw cost data
        extracted = []
        for service in services:
            match = next(
                (
                    item for item in results
                    if item.get("Keys") and service.lower() in item["Keys"][0].lower()
                ),
                None,
            )
            if match:
                metric = self._get_metric(match.get("Metrics", {}))
                if metric:
                    amount = metric.get("Amount", "0")
                    unit = metric.get("Unit", "USD")
                    extracted.append(f"{service}: {amount} {unit}")
                else:
                    extracted.append(f"{service}: Metric not found")
            else:
                extracted.append(f"{service}: Not found")

        # Use GPT to summarize into natural language
        prompt = (
            "Summarize the following AWS cost data in a clear, user-friendly way:\n\n"
            + "\n".join(extracted)
        )

        completion = self.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that explains AWS billing data."},
                {"role": "user", "content": prompt}
            ]
        )

        return completion.choices[0].message.content
