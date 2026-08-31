"""多服务商注册表与引擎适配的离线单元测试（不打网络）。"""
from __future__ import annotations

import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.ai_engine import PainIntelEngine
from src.llm_providers import DEFAULT_PROVIDER, PROVIDERS


class ProviderRegistryTest(unittest.TestCase):
    def test_default_provider_exists(self):
        self.assertIn(DEFAULT_PROVIDER, PROVIDERS)

    def test_registry_fields_complete(self):
        for pid, p in PROVIDERS.items():
            with self.subTest(provider=pid):
                self.assertTrue(p["label"], pid)
                self.assertTrue(p["short"], pid)
                self.assertIsInstance(p["models"], list, pid)
                self.assertIsInstance(p["key_env"], (str, type(None)), pid)
                self.assertIsInstance(p["key_hint"], str, pid)
                base = p["base_url"]
                if pid == "custom":
                    self.assertEqual(base, "")  # 自定义端点由用户填写
                else:
                    self.assertTrue(base.startswith("http"), pid)
                    self.assertFalse(base.endswith("/"), pid)  # 引擎会再拼 /chat/completions

    def test_ollama_needs_no_key(self):
        self.assertIsNone(PROVIDERS["ollama"]["key_env"])

    def test_key_env_names_unique_and_uppercase(self):
        envs = [p["key_env"] for p in PROVIDERS.values() if p["key_env"]]
        self.assertEqual(len(envs), len(set(envs)))
        for env in envs:
            self.assertEqual(env, env.upper())


class EngineAdaptTest(unittest.TestCase):
    def test_openrouter_attribution_headers(self):
        eng = PainIntelEngine("https://openrouter.ai/api/v1", "m", "k")
        headers = eng._headers()
        self.assertEqual(headers["Authorization"], "Bearer k")
        self.assertIn("HTTP-Referer", headers)
        self.assertIn("X-Title", headers)

    def test_other_provider_has_no_attribution_headers(self):
        eng = PainIntelEngine("https://api.openai.com/v1/", "gpt-4o", "k")
        headers = eng._headers()
        self.assertNotIn("HTTP-Referer", headers)
        self.assertNotIn("X-Title", headers)
        self.assertEqual(eng.base_url, "https://api.openai.com/v1")  # 去除末尾斜杠

    def test_key_fallback_to_llm_api_key_env(self):
        with mock.patch.dict(os.environ, {"LLM_API_KEY": "generic-key"}):
            eng = PainIntelEngine("https://api.deepseek.com/v1", "deepseek-chat")
            self.assertEqual(eng.api_key, "generic-key")

    def test_explicit_key_wins_over_env(self):
        env = {"LLM_API_KEY": "generic-key", "OPENROUTER_API_KEY": "or-key"}
        with mock.patch.dict(os.environ, env):
            eng = PainIntelEngine("https://api.openai.com/v1", "gpt-4o", "explicit-key")
            self.assertEqual(eng.api_key, "explicit-key")

    def test_missing_key_raises(self):
        env = {"LLM_API_KEY": "", "OPENROUTER_API_KEY": ""}
        with mock.patch.dict(os.environ, env):
            os.environ.pop("LLM_API_KEY", None)
            os.environ.pop("OPENROUTER_API_KEY", None)
            with self.assertRaises(ValueError):
                PainIntelEngine("https://api.openai.com/v1", "gpt-4o", "")


if __name__ == "__main__":
    unittest.main()
