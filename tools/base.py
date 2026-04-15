"""BaseTool — 모든 도구의 추상 베이스 클래스"""

from abc import ABC, abstractmethod
from typing import Callable
import subprocess
import os


class BaseTool(ABC):
    tool_id: str = ""
    name: str = ""
    requires_admin: bool = True
    requires_reboot: bool = False

    @abstractmethod
    def run(self, log: Callable[[str, int], None]) -> bool:
        """
        도구 실행.

        Args:
            log: 로그 콜백 (message, step_index).
                 step_index=-1 일반 로그, >=0 해당 단계 완료 표시.
        Returns:
            True=성공, False=실패
        """
        pass

    def get_steps(self) -> list[str]:
        """실행 단계 목록 (진행률 표시용)"""
        return []

    # ── 공통 헬퍼 ──

    def _run_cmd(self, cmd: str, log: Callable,
                 timeout: int = 30) -> tuple[int, str]:
        """subprocess 명령 실행 (UTF-8 강제)"""
        try:
            # chcp 65001: cmd.exe 출력을 UTF-8로 강제
            full_cmd = f"chcp 65001 >nul && {cmd}"
            result = subprocess.run(
                full_cmd, shell=True, capture_output=True,
                text=True, timeout=timeout, encoding="utf-8",
                errors="replace",
            )
            log(f"$ {cmd}", -1)
            out = result.stdout.strip()
            if out:
                log(f"  {out[:200]}", -1)
            return result.returncode, result.stdout
        except subprocess.TimeoutExpired:
            log(f"시간 초과: {cmd}", -1)
            return -1, "timeout"
        except Exception as e:
            log(f"명령 오류: {e}", -1)
            return -1, str(e)

    def _run_ps(self, script: str, log: Callable,
                timeout: int = 30) -> tuple[int, str]:
        """PowerShell 스크립트 실행 (UTF-8 출력 강제)"""
        # [Console]::OutputEncoding으로 PS 출력도 UTF-8 강제
        utf8_prefix = (
            "[Console]::OutputEncoding="
            "[System.Text.Encoding]::UTF8; "
        )
        cmd = (
            f'powershell -NoProfile -ExecutionPolicy Bypass '
            f'-Command "{utf8_prefix}{script}"'
        )
        return self._run_cmd(cmd, log, timeout)

    def _stop_service(self, name: str, log: Callable) -> bool:
        code, _ = self._run_cmd(f"net stop {name}", log)
        return code == 0

    def _start_service(self, name: str, log: Callable) -> bool:
        code, _ = self._run_cmd(f"net start {name}", log)
        return code == 0

    def _delete_files(self, directory: str, log: Callable,
                      pattern: str = "*") -> int:
        """디렉토리 내 파일 삭제 (사용 중 파일 skip)"""
        import glob
        deleted = 0
        for f in glob.glob(os.path.join(directory, pattern)):
            try:
                if os.path.isfile(f):
                    os.remove(f)
                    deleted += 1
            except PermissionError:
                pass
            except Exception as e:
                log(f"  삭제 실패: {os.path.basename(f)} ({e})", -1)
        return deleted
