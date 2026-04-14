"""실행 로그 관리 (JSONL 월별 파일)"""

import json
import os
from datetime import datetime


class ToolLogger:
    def __init__(self, log_dir: str = "data/logs"):
        self._log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)

    def log_execution(self, tool_id: str, tool_name: str,
                      symptom_title: str, success: bool,
                      duration_sec: float, error_msg: str = "",
                      steps: list[dict] | None = None):
        entry = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "tool_id": tool_id,
            "tool_name": tool_name,
            "symptom_title": symptom_title,
            "success": success,
            "duration_sec": round(duration_sec, 1),
            "error_msg": error_msg,
            "steps": steps or [],
        }
        filename = datetime.now().strftime("%Y-%m") + ".jsonl"
        filepath = os.path.join(self._log_dir, filename)
        with open(filepath, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def get_recent(self, limit: int = 30) -> list[dict]:
        """최근 실행 기록 (최신 순)"""
        if not os.path.isdir(self._log_dir):
            return []
        entries: list[dict] = []
        files = sorted(
            [f for f in os.listdir(self._log_dir) if f.endswith(".jsonl")],
            reverse=True,
        )
        for fname in files:
            path = os.path.join(self._log_dir, fname)
            with open(path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        entries.append(json.loads(line))
            if len(entries) >= limit * 2:
                break
        entries.sort(key=lambda e: e["timestamp"], reverse=True)
        return entries[:limit]
