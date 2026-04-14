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

    # 삭제 전 C:\setup\으로 복사할 설치 파일
    INSTALLER_FILES = [
        "MSYSTECH_ServerInfo.ini",
        "M.CMM.ServerInfo.exe",
        "M.CMM.ServerInfo.exe.config",
        "TXTextControl.Server.dll",
        "M.CMM.ServerInfo_32bit.exe",
        "M.CMM.LiveUpdate.pdb",
        "M.CMM.LiveUpdate.exe",
    ]

    def get_steps(self):
        return [
            "EMR 프로세스 종료",
            "설치 파일 백업 (bin → C:\\setup)",
            "기존 EMR 폴더 삭제",
            "EMR 재설치 실행",
        ]

    def run(self, log):
        # Step 0: EMR 프로세스 종료
        self._run_cmd("taskkill /F /IM M.HIS.HISMainEXE_32bit.exe", log, timeout=10)
        self._run_cmd("taskkill /F /IM M.CMM.LiveUpdate.exe", log, timeout=10)
        log("EMR 프로세스 종료 완료", 0)

        # Step 1: 설치 파일을 EMR bin → C:\setup\ 으로 복사
        if not os.path.isdir(self.EMR_BIN):
            log(f"EMR bin 폴더를 찾을 수 없습니다: {self.EMR_BIN}", -1)
            log("EMR이 설치되어 있지 않습니다. 전산팀에 문의하세요.", -1)
            return False

        os.makedirs(self.SETUP_DIR, exist_ok=True)
        copied = 0
        for fname in self.INSTALLER_FILES:
            src = os.path.join(self.EMR_BIN, fname)
            dst = os.path.join(self.SETUP_DIR, fname)
            if os.path.isfile(src):
                try:
                    shutil.copy2(src, dst)
                    copied += 1
                    log(f"  복사: {fname}", -1)
                except Exception as e:
                    log(f"  복사 실패: {fname} ({e})", -1)

        if not os.path.isfile(self.LIVE_UPDATE):
            log("LiveUpdate.exe 복사에 실패했습니다. EMR 폴더를 삭제하지 않고 중단합니다.", -1)
            log("전산팀에 문의하세요.", -1)
            return False

        log(f"설치 파일 {copied}개 백업 완료 → C:\\setup\\", 1)

        # Step 2: 기존 EMR 폴더 삭제
        try:
            shutil.rmtree(self.EMR_DIR, ignore_errors=True)
            log("기존 EMR 폴더 삭제 완료", 2)
        except Exception as e:
            log(f"EMR 폴더 삭제 중 오류: {e}", -1)
            log("일부 파일이 사용 중일 수 있습니다", -1)

        # Step 3: LiveUpdate로 재설치
        self._run_cmd(f'start "" "{self.LIVE_UPDATE}"', log, timeout=10)
        log("EMR LiveUpdate 실행됨 — 자동 설치가 진행됩니다", 3)
        return True
