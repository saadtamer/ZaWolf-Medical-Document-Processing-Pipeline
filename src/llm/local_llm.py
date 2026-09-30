import json
import os
import requests
import requests.adapters


def get_optimal_thread_count():
    try:
        import psutil
        physical = psutil.cpu_count(logical=False)
        if physical and physical > 0:
            return physical
    except Exception:
        pass
    logical = os.cpu_count() or 4
    return max(1, logical // 2 if logical > 2 else logical)


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
        self._session = None
        self.threads = get_optimal_thread_count()

    def _get_session(self):
        if self._session is None:
            self._session = requests.Session()
            adapter = requests.adapters.HTTPAdapter(
                pool_connections=1,
                pool_maxsize=2,
                max_retries=1
            )
            self._session.mount("http://", adapter)
            self._session.mount("https://", adapter)
        return self._session

    def close(self):
        """Explicitly closes the HTTP session and frees socket handles immediately."""
        if self._session is not None:
            try:
                self._session.close()
            except Exception:
                pass
            self._session = None

    def __del__(self):
        self.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def generate(self, prompt, system_prompt=None):
        print("\n===== LLM DEBUG =====")
        print(f"Model: {self.model}")
        print(f"Threads: {self.threads} (auto-detected)")
        print(f"Prompt length: {len(prompt):,} chars")

        if system_prompt:
            print(f"System prompt length: {len(system_prompt):,} chars")

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "think": False,
            "options": {
                "num_ctx": 16384,
                "num_predict": 2048,
                "temperature": 0.0,
                "num_thread": self.threads
            }
        }

        if system_prompt:
            payload["system"] = system_prompt

        response = self._get_session().post(
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