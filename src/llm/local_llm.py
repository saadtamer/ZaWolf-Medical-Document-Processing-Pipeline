import json
import requests


class LocalLLM:
    def __init__(
        self,
        model="qwen3:latest",
        base_url="http://localhost:11434",
        timeout=600
    ):
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def generate(self, prompt, system_prompt=None):
        print("\n===== LLM DEBUG =====")
        print(f"Model: {self.model}")
        print(f"Prompt length: {len(prompt):,} chars")

        if system_prompt:
            print(f"System prompt length: {len(system_prompt):,} chars")

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "think": False
        }

        if system_prompt:
            payload["system"] = system_prompt

        response = requests.post(
            f"{self.base_url}/api/generate",
            json=payload,
            timeout=self.timeout
        )

        response.raise_for_status()

        result = response.json()

        if "response" not in result:
            raise ValueError("LLM response field is missing.")

        response_text = result["response"]

        print(f"Response length: {len(response_text):,} chars")
        print("===== END LLM DEBUG =====\n")

        return response_text

    def generate_json(self, prompt, system_prompt=None):
        response_text = self.generate(
            prompt=prompt,
            system_prompt=system_prompt
        )

        try:
            return json.loads(response_text)
        except json.JSONDecodeError as error:
            print("\n===== INVALID JSON RESPONSE =====")
            print(response_text)
            print("===== END INVALID JSON RESPONSE =====\n")

            raise ValueError(
                f"LLM returned invalid JSON: {error}"
            ) from error