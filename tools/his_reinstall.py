"""⑭ HIS(EMR) 재설치"""

import os
import shutil
from tools.base import BaseTool


class HisReinstallTool(BaseTool):
    tool_id = "his_reinstall"
    name = "EMR 재설치"
    requires_admin = True
    requires_reboot = False

    # EMR 경로 (서울재활병원 표준)
    EMR_DIR = r"C:\MsystechHIS_Ver.2"
    EMR_BIN = r"C:\MsystechHIS_Ver.2\bin"
    SETUP_DIR = r"C:\setup"
    LIVE_UPDATE = r"C:\setup\M.CMM.LiveUpdate.exe"

    # 백업 대상 설정 파일
    BACKUP_FILES = [
        "ServerInfo.ini",
        "HISConfig.ini",
        "Connection.ini",
    ]

    def get_steps(self):
        return [
            "사전 검증",
            "EMR 프로세스 종료",
            "설정 파일 백업",
            "기존 EMR 폴더 삭제",
            "EMR 재설치 실행",
        ]

    def run(self, log):
        # Step 0: 사전 검증 — LiveUpdate 없으면 삭제하지 않고 중단
        if not os.path.isfile(self.LIVE_UPDATE):
            log(f"LiveUpdate를 찾을 수 없습니다: {self.LIVE_UPDATE}", -1)
            log("EMR 폴더를 삭제하지 않고 중단합니다", -1)
            log("전산팀에 문의하여 C:\\setup\\M.CMM.LiveUpdate.exe 파일을 받으세요", -1)
            return False
        log("LiveUpdate 확인 완료", 0)

        # Step 1: EMR 프로세스 종료
        self._run_cmd("taskkill /F /IM M.HIS.HISMainEXE_32bit.exe", log, timeout=10)
        self._run_cmd("taskkill /F /IM M.CMM.LiveUpdate.exe", log, timeout=10)
        log("EMR 프로세스 종료 완료", 1)

        # Step 2: 설정 파일 백업
        os.makedirs(self.SETUP_DIR, exist_ok=True)
        backed_up = 0
        for fname in self.BACKUP_FILES:
            src = os.path.join(self.EMR_BIN, fname)
            dst = os.path.join(self.SETUP_DIR, fname)
            if os.path.isfile(src):
                try:
                    shutil.copy2(src, dst)
                    backed_up += 1
                    log(f"  백업: {fname}", -1)
                except Exception as e:
                    log(f"  백업 실패: {fname} ({e})", -1)

        log(f"설정 파일 {backed_up}개 백업 완료 → C:\\setup\\", 2)

        # Step 3: 기존 EMR 폴더 삭제
        if os.path.isdir(self.EMR_DIR):
            try:
                shutil.rmtree(self.EMR_DIR, ignore_errors=True)
                log("기존 EMR 폴더 삭제 완료", 3)
            except Exception as e:
                log(f"EMR 폴더 삭제 중 오류: {e}", -1)
                log("일부 파일이 사용 중일 수 있습니다", -1)
        else:
            log("EMR 폴더 없음 (이미 삭제됨)", 3)

        # Step 4: LiveUpdate로 재설치
        code, output = self._run_cmd(
            f'start "" "{self.LIVE_UPDATE}"', log, timeout=10,
        )
        log("EMR LiveUpdate 실행됨 — 자동 설치가 진행됩니다", 4)
        return True
