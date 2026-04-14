"""pywebview JS API -- Python 백엔드 브릿지"""

import json
import os
import sys
import threading
import time
import webbrowser

import config
from core.logger import ToolLogger
from tools.registry import get_tool


class WebViewAPI:
    """pywebview JS <-> Python 브릿지 API

    JS에서 window.pywebview.api.method_name() 으로 호출.
    모든 메서드는 JSON-serializable 값을 반환해야 함.
    """

    def __init__(self):
        self._window = None
        self._logger = ToolLogger(self._resolve_path(config.LOG_DIR))
        self._symptom_map = self._load_symptom_map()

    def set_window(self, window):
        self._window = window

    # -- 경로 --

    def _resolve_path(self, rel_path: str) -> str:
        if getattr(sys, "frozen", False):
            base = os.path.dirname(sys.executable)
        else:
            base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(base, rel_path)

    # -- 데이터 로드 --

    def _load_symptom_map(self) -> dict:
        path = self._resolve_path(config.SYMPTOM_MAP_FILE)
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[WARN] symptom_map.json load fail: {e}")
            return {
                "version": "fallback",
                "remote_support": {
                    "url": config.REMOTE_SUPPORT_URL,
                    "label": "원격 지원 요청",
                },
                "categories": [],
                "tag_labels": {},
            }

    # -- JS API --

    def get_config(self) -> dict:
        rs = self._symptom_map.get("remote_support", {})
        return {
            "app_name": config.APP_NAME,
            "app_version": config.APP_VERSION,
            "author": config.AUTHOR,
            "remote_url": rs.get("url", config.REMOTE_SUPPORT_URL),
        }

    def get_symptom_map(self) -> dict:
        return self._symptom_map

    def get_tool_info(self, tool_id: str) -> dict:
        tool = get_tool(tool_id)
        if not tool:
            return {}
        return {
            "tool_id": tool.tool_id,
            "name": tool.name,
            "requires_admin": tool.requires_admin,
            "requires_reboot": tool.requires_reboot,
            "steps": tool.get_steps(),
        }

    def get_history(self, limit: int = 30) -> list:
        return self._logger.get_recent(limit)

    def open_url(self, url: str):
        webbrowser.open(url)

    def execute_tool(self, symptom_json: str):
        """도구 실행 (백그라운드 스레드)"""
        symptom = json.loads(symptom_json)
        tool_id = symptom.get("tool_id", "")
        tool = get_tool(tool_id)
        if not tool:
            self._push_js("onToolComplete(false, 0, false)")
            return

        thread = threading.Thread(
            target=self._run_tool, args=(symptom, tool), daemon=True,
        )
        thread.start()

    # -- 내부 --

    def _run_tool(self, symptom: dict, tool):
        start = time.time()

        def log_cb(message: str, step_index: int = -1):
            safe = json.dumps(message, ensure_ascii=False)
            self._push_js(f"onToolLog({safe}, {step_index})")

        try:
            success = tool.run(log=log_cb)
        except Exception as e:
            log_cb(f"오류 발생: {e}", -1)
            success = False

        duration = time.time() - start

        self._logger.log_execution(
            tool_id=symptom.get("tool_id", ""),
            tool_name=tool.name,
            symptom_title=symptom.get("title", ""),
            success=success,
            duration_sec=duration,
        )

        self._push_js(
            f"onToolComplete({json.dumps(success)}, {duration:.1f}, "
            f"{json.dumps(tool.requires_reboot)})"
        )

    def _push_js(self, js_code: str):
        if self._window:
            try:
                self._window.evaluate_js(js_code)
            except Exception:
                pass
