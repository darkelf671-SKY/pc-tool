"""⑬ MS 계정 초기화 (WAM 인프라 보존)"""

import os
import glob
from tools.base import BaseTool


class MsAccountCleanupTool(BaseTool):
    tool_id = "ms_account_cleanup"
    name = "MS 계정 초기화"
    requires_admin = True
    requires_reboot = False

    def get_steps(self):
        return ["자격 증명 정리", "AAD/MSA 캐시 삭제",
                "토큰 브로커 캐시 삭제"]

    def run(self, log):
        # Step 0: Windows 자격 증명 관리자 — MS 관련 자격증명 정리
        ps_cred = (
            "$targets = @('MicrosoftAccount:*','MicrosoftOffice*',"
            "'OneDrive*','SSO_POP_Device*','virtualapp/didlogical*'); "
            "$removed = 0; "
            "foreach ($p in $targets) { "
            "  $lines = cmdkey /list 2>$null | Select-String $p; "
            "  foreach ($l in $lines) { "
            "    $t = ($l -split 'Target:\\s*')[1]; "
            "    if ($t) { cmdkey /delete:$t 2>$null; $removed++ } "
            "  } "
            "}; "
            "Write-Output \"REMOVED:$removed\""
        )
        code, output = self._run_ps(ps_cred, log, timeout=30)
        log("자격 증명 정리 완료", 0)

        # Step 1: AAD/MSA 캐시 토큰 삭제
        # ⚠️ WAM 인프라(Authentication, WebAccountManager) 절대 삭제 금지
        local = os.environ.get("LOCALAPPDATA", "")
        patterns = [
            os.path.join(local, "Packages", "Microsoft.AAD.BrokerPlugin_*"),
            os.path.join(
                local, "Packages",
                "Microsoft.Windows.CloudExperienceHost_*",
            ),
        ]
        deleted = 0
        for pat in patterns:
            for pkg_dir in glob.glob(pat):
                accounts_dir = os.path.join(
                    pkg_dir, "AC", "TokenBroker", "Accounts"
                )
                if os.path.isdir(accounts_dir):
                    for f in os.listdir(accounts_dir):
                        fp = os.path.join(accounts_dir, f)
                        try:
                            os.remove(fp)
                            deleted += 1
                        except Exception:
                            pass
        log(f"AAD/MSA 캐시 토큰 {deleted}개 삭제", 1)

        # Step 2: TokenBroker 캐시
        tbr_path = os.path.join(
            local, "Microsoft", "TokenBroker", "Cache"
        )
        tbr_del = 0
        if os.path.isdir(tbr_path):
            for f in os.listdir(tbr_path):
                if f.endswith(".tbres"):
                    try:
                        os.remove(os.path.join(tbr_path, f))
                        tbr_del += 1
                    except Exception:
                        pass
        log(f"토큰 브로커 캐시 {tbr_del}개 삭제 완료", 2)
        return True
