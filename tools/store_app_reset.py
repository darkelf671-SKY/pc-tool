"""⑧ MS Store 앱 초기화"""

from tools.base import BaseTool


class StoreAppResetTool(BaseTool):
    tool_id = "store_app_reset"
    name = "MS Store 앱 초기화"
    requires_admin = True
    requires_reboot = False

    def get_steps(self):
        return ["Store 캐시 초기화", "Store 앱 재등록"]

    def run(self, log):
        # Step 0: wsreset
        self._run_cmd("wsreset.exe", log)
        log("Store 캐시 초기화 완료", 0)

        # Step 1: 앱 재등록
        ps = (
            "Get-AppxPackage -AllUsers | "
            "Where-Object {$_.Name -notlike '*Teams*'} | "
            "ForEach-Object {"
            "Add-AppxPackage -DisableDevelopmentMode "
            "-Register \"$($_.InstallLocation)\\AppxManifest.xml\" "
            "-ErrorAction SilentlyContinue"
            "}"
        )
        self._run_ps(ps, log, timeout=120)
        log("Store 앱 재등록 완료 (Teams 제외)", 1)
        return True
