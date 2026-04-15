"""⑬ MS 계정 초기화 — pc-setup 13-resign-cleanup.ps1 v6 완전 이식

10단계 외과적 정밀 삭제:
  0. WAM 인프라 백업
  1. 프로세스 + TokenBroker 서비스 종료
  2. HKCU 레지스트리 (계정 데이터만, WAM 인프라 보존)
  3. HKLM 레지스트리 (관리자)
  4. 자격 증명 관리자 (10개 패턴)
  5. 파일 캐시 (외과적 삭제)
  6. Edge 완전 초기화
  7. Chrome 완전 초기화
  8. Teams 완전 삭제
  9. WAM 검증 + 자동 복구
"""

import os
import glob
import shutil
import time
from tools.base import BaseTool

# 자격 증명 관리자 필터 패턴
_CREDENTIAL_PATTERNS = [
    "Microsoft", "Azure", "Office", "Teams",
    "outlook", "login.live", "O365",
    "OneDrive", "SharePoint", "MicrosoftAccount",
]

# 종료할 프로세스 목록
_MS_PROCESSES = [
    "Teams", "ms-teams",
    "msedge", "chrome",
    "OUTLOOK", "EXCEL", "WINWORD", "POWERPNT", "ONENOTE",
    "OneDrive",
    "Microsoft.AAD.BrokerPlugin",
    "backgroundTaskHost",
    "CompPkgSrv", "dllhost",
]

# HKCU 삭제 대상 (키 자체 삭제 OK — 앱이 재생성)
_HKCU_DELETE_PATHS = [
    r"HKCU:\Software\Microsoft\Windows NT\CurrentVersion\WorkplaceJoin\JoinInfo",
    r"HKCU:\Software\Microsoft\Windows NT\CurrentVersion\WorkplaceJoin\TenantInfo",
    r"HKCU:\Software\Microsoft\Office\16.0\Common\Identity",
    r"HKCU:\Software\Microsoft\Teams",
    r"HKCU:\Software\Microsoft\Windows\CurrentVersion\CDP\CdpSessionSignIn",
]

# HKCU 정밀 삭제 (하위 키 내용만 삭제, 키 자체 보존)
_HKCU_SURGICAL = {
    r"HKCU:\Software\Microsoft\IdentityCRL": ["StoredIdentities", "OAuthToken"],
    r"HKCU:\Software\Microsoft\Windows\CurrentVersion\TokenBroker": ["Accounts", "Cache"],
    r"HKCU:\Software\Microsoft\Windows\CurrentVersion\AAD": ["Storage"],
}

# HKLM 정밀 삭제 (하위 키 내용만)
_HKLM_PATHS = [
    r"HKLM:\SOFTWARE\Microsoft\IdentityCRL\StoredIdentities",
    r"HKLM:\SOFTWARE\Microsoft\IdentityCRL\UserExtendedProperties",
    r"HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Authentication\LogonUI\SessionData",
]

# WAM 인프라 키 (절대 삭제 금지, 백업+검증 대상)
_WAM_KEYS = [
    {
        "path": r"HKCU:\Software\Microsoft\Windows\CurrentVersion\Authentication",
        "file": "Authentication.reg",
        "reg_path": r"HKCU\Software\Microsoft\Windows\CurrentVersion\Authentication",
    },
    {
        "path": r"HKCU:\Software\Microsoft\Windows\CurrentVersion\WebAccountManager",
        "file": "WebAccountManager.reg",
        "reg_path": r"HKCU\Software\Microsoft\Windows\CurrentVersion\WebAccountManager",
    },
]


class MsAccountCleanupTool(BaseTool):
    tool_id = "ms_account_cleanup"
    name = "MS 계정 초기화"
    requires_admin = True
    requires_reboot = True

    def get_steps(self):
        return [
            "WAM 인프라 백업",
            "프로세스 및 서비스 종료",
            "HKCU 레지스트리 정밀 삭제",
            "HKLM 레지스트리 정밀 삭제",
            "자격 증명 관리자 정리",
            "토큰/캐시 파일 정밀 삭제",
            "Edge 완전 초기화",
            "Chrome 완전 초기화",
            "Teams 완전 삭제",
            "WAM 검증 + 자동 복구",
        ]

    def run(self, log):
        local = os.environ.get("LOCALAPPDATA", "")
        appdata = os.environ.get("APPDATA", "")
        temp = os.environ.get("TEMP", "")
        backup_dir = os.path.join(temp, "wam-backup")

        # ── [0/9] WAM 인프라 백업 ──
        os.makedirs(backup_dir, exist_ok=True)
        backed = 0
        for wk in _WAM_KEYS:
            ps = (
                f"if (Test-Path '{wk['path']}') {{ "
                f"  reg export '{wk['reg_path']}' '{os.path.join(backup_dir, wk['file'])}' /y 2>&1 | Out-Null; "
                f"  Write-Output 'OK' "
                f"}} else {{ Write-Output 'MISSING' }}"
            )
            code, out = self._run_ps(ps, log, timeout=10)
            if "OK" in out:
                backed += 1
                log(f"  백업: {wk['file']}", -1)
            else:
                log(f"  [!] {wk['file'].replace('.reg','')} 키 없음 — 이미 손상 상태", -1)
        log(f"WAM 인프라 {backed}개 백업 완료", 0)

        # ── [1/9] 프로세스 + TokenBroker 서비스 종료 ──
        killed = 0
        for proc in _MS_PROCESSES:
            ps = (
                f"$p = Get-Process -Name '{proc}' -ErrorAction SilentlyContinue; "
                f"if ($p) {{ $p | Stop-Process -Force -ErrorAction SilentlyContinue; "
                f"Write-Output \"KILLED:$($p.Count)\" }} else {{ Write-Output 'NONE' }}"
            )
            code, out = self._run_ps(ps, log, timeout=10)
            if "KILLED" in out:
                killed += 1
        # TokenBroker 서비스 중지 (재생성 방지 핵심)
        self._run_ps(
            "try { Stop-Service -Name 'TokenBroker' -Force -ErrorAction Stop; "
            "Write-Output 'STOPPED' } catch { Write-Output 'SKIP' }",
            log, timeout=10,
        )
        time.sleep(3)
        log(f"프로세스 {killed}종 + TokenBroker 서비스 종료", 1)

        # ── [2/9] HKCU 레지스트리 정밀 삭제 ──
        cleaned = 0
        # (A) 앱 데이터 키 — 키 자체 삭제 OK
        for path in _HKCU_DELETE_PATHS:
            ps = (
                f"if (Test-Path '{path}') {{ "
                f"  Remove-Item '{path}' -Recurse -Force -ErrorAction SilentlyContinue; "
                f"  Write-Output 'DELETED' "
                f"}} else {{ Write-Output 'NONE' }}"
            )
            code, out = self._run_ps(ps, log, timeout=10)
            if "DELETED" in out:
                cleaned += 1
                key_name = path.rsplit("\\", 1)[-1]
                log(f"  삭제: {key_name}", -1)

        # (B~E) 정밀 삭제 — 하위 키 내용만 삭제, 키 구조 보존
        for base, subkeys in _HKCU_SURGICAL.items():
            for sub in subkeys:
                full = f"{base}\\{sub}"
                ps = (
                    f"if (Test-Path '{full}') {{ "
                    f"  Get-ChildItem '{full}' -EA SilentlyContinue | "
                    f"  Remove-Item -Recurse -Force -EA SilentlyContinue; "
                    f"  Write-Output 'CLEANED' "
                    f"}} else {{ Write-Output 'NONE' }}"
                )
                code, out = self._run_ps(ps, log, timeout=10)
                if "CLEANED" in out:
                    cleaned += 1
                    base_name = base.rsplit("\\", 1)[-1]
                    log(f"  정밀삭제: {base_name}\\{sub}", -1)

        # CDP 전체 하위 삭제
        cdp = r"HKCU:\Software\Microsoft\Windows\CurrentVersion\CDP"
        ps = (
            f"if (Test-Path '{cdp}') {{ "
            f"  Get-ChildItem '{cdp}' -EA SilentlyContinue | "
            f"  Remove-Item -Recurse -Force -EA SilentlyContinue; "
            f"  Write-Output 'CLEANED' "
            f"}} else {{ Write-Output 'NONE' }}"
        )
        code, out = self._run_ps(ps, log, timeout=10)
        if "CLEANED" in out:
            cleaned += 1
            log("  정밀삭제: CDP 하위 (세션 데이터)", -1)

        log(f"  [유지] Authentication, WebAccountManager (WAM 인프라)", -1)
        log(f"HKCU {cleaned}개 경로 정리 완료", 2)

        # ── [3/9] HKLM 레지스트리 (관리자) ──
        lm_cleaned = 0
        for path in _HKLM_PATHS:
            ps = (
                f"if (Test-Path '{path}') {{ "
                f"  try {{ "
                f"    Get-ChildItem '{path}' -ErrorAction SilentlyContinue | "
                f"    Remove-Item -Recurse -Force -ErrorAction Stop; "
                f"    Write-Output 'DELETED' "
                f"  }} catch {{ Write-Output 'FAIL' }} "
                f"}} else {{ Write-Output 'NONE' }}"
            )
            code, out = self._run_ps(ps, log, timeout=10)
            if "DELETED" in out:
                lm_cleaned += 1
                key_name = path.rsplit("\\", 1)[-1]
                log(f"  삭제: {key_name}", -1)

        # Workplace Join 해제 (Azure AD Joined은 유지)
        ps_dsreg = (
            "$d = dsregcmd /status 2>&1 | Out-String; "
            "$aad = $d -match 'AzureAdJoined\\s*:\\s*YES'; "
            "$wp = $d -match 'WorkplaceJoined\\s*:\\s*YES'; "
            "if ($aad) { Write-Output 'AAD_JOINED' }; "
            "if ($wp) { dsregcmd /leave 2>&1 | Out-Null; Write-Output 'WP_LEFT' }; "
            "if (-not $aad -and -not $wp) { Write-Output 'NONE' }"
        )
        code, out = self._run_ps(ps_dsreg, log, timeout=15)
        if "AAD_JOINED" in out:
            log("  [유지] Azure AD Joined — 조직 장치 등록 유지", -1)
        if "WP_LEFT" in out:
            log("  [해제] Workplace Join — 개인 계정 연결 해제", -1)
        log(f"HKLM {lm_cleaned}개 경로 정리 완료", 3)

        # ── [4/9] 자격 증명 관리자 ──
        patterns_str = "|".join(_CREDENTIAL_PATTERNS)
        ps_cred = (
            "$removed = 0; $cur = ''; "
            "$lines = cmdkey /list 2>&1; "
            "foreach ($l in ($lines -split \"`n\")) { "
            "  if ($l -match '^\\s*(Target|대상)\\s*:\\s*(.+)$') { $cur = $Matches[2].Trim() }; "
            f"  if ($cur -and ($cur -match '{patterns_str}')) {{ "
            "    cmdkey /delete:\"$cur\" 2>&1 | Out-Null; $removed++; $cur = '' "
            "  } "
            "}; "
            "Write-Output \"REMOVED:$removed\""
        )
        code, out = self._run_ps(ps_cred, log, timeout=30)
        removed = 0
        if "REMOVED:" in out:
            try:
                removed = int(out.split("REMOVED:")[1].strip().split()[0])
            except (ValueError, IndexError):
                pass
        log(f"자격 증명 {removed}개 삭제 완료", 4)

        # ── [5/9] 파일 캐시 정밀 삭제 ──
        cache_cleaned = 0

        # (A) TokenBroker 파일 캐시: Accounts 폴더만
        tb_accounts = os.path.join(local, "Microsoft", "TokenBroker", "Accounts")
        if os.path.isdir(tb_accounts):
            cache_cleaned += self._clear_folder_contents(tb_accounts)
            log("  정밀삭제: TokenBroker\\Accounts (토큰 파일)", -1)

        # (B) 순수 캐시 폴더 — 내용 삭제 (폴더 유지)
        for name in ["IdentityCache", "Credentials", "OneAuth"]:
            path = os.path.join(local, "Microsoft", name)
            if os.path.isdir(path):
                cache_cleaned += self._clear_folder_contents(path)
                log(f"  내용 삭제: {name} (폴더 유지)", -1)

        # (C) ConnectedDevicesPlatform — 폴더째 삭제
        cdp_path = os.path.join(local, "ConnectedDevicesPlatform")
        if os.path.isdir(cdp_path):
            shutil.rmtree(cdp_path, ignore_errors=True)
            cache_cleaned += 1
            log("  삭제: ConnectedDevicesPlatform", -1)

        # (D) AAD BrokerPlugin — Accounts 폴더만 (플러그인 상태 보존!)
        for pkg_dir in glob.glob(os.path.join(local, "Packages", "Microsoft.AAD.BrokerPlugin_*")):
            acct = os.path.join(pkg_dir, "AC", "TokenBroker", "Accounts")
            if os.path.isdir(acct):
                cache_cleaned += self._clear_folder_contents(acct)
                log("  정밀삭제: AAD.BrokerPlugin\\TokenBroker\\Accounts", -1)

        # (E) CloudExperienceHost — Accounts 폴더만
        for pkg_dir in glob.glob(os.path.join(local, "Packages", "Microsoft.Windows.CloudExperienceHost_*")):
            acct = os.path.join(pkg_dir, "AC", "TokenBroker", "Accounts")
            if os.path.isdir(acct):
                cache_cleaned += self._clear_folder_contents(acct)
                log("  정밀삭제: CloudExperienceHost\\TokenBroker\\Accounts", -1)

        log(f"캐시 {cache_cleaned}개 항목 정리 완료", 5)

        # ── [6/9] Edge 완전 초기화 ──
        edge_data = os.path.join(local, "Microsoft", "Edge", "User Data")
        if os.path.isdir(edge_data):
            # Edge 프로세스 재확인
            self._run_cmd("taskkill /F /IM msedge.exe", log, timeout=5)
            time.sleep(2)
            shutil.rmtree(edge_data, ignore_errors=True)
            if not os.path.isdir(edge_data):
                log("Edge User Data 전체 삭제 완료", 6)
            else:
                # 잠긴 파일 있으면 가능한 것만 삭제
                self._force_delete_dir(edge_data, log)
                log("Edge User Data 부분 삭제 (잠긴 파일 — 재부팅 후 완료)", 6)
        else:
            log("Edge 미설치", 6)

        # ── [7/9] Chrome 완전 초기화 ──
        chrome_data = os.path.join(local, "Google", "Chrome", "User Data")
        if os.path.isdir(chrome_data):
            self._run_cmd("taskkill /F /IM chrome.exe", log, timeout=5)
            time.sleep(2)
            shutil.rmtree(chrome_data, ignore_errors=True)
            if not os.path.isdir(chrome_data):
                log("Chrome User Data 전체 삭제 완료", 7)
            else:
                self._force_delete_dir(chrome_data, log)
                log("Chrome User Data 부분 삭제 (잠긴 파일 — 재부팅 후 완료)", 7)
        else:
            log("Chrome 미설치", 7)

        # ── [8/9] Teams 완전 삭제 ──
        teams_cleaned = 0

        # Classic Teams (%APPDATA%)
        old_teams = os.path.join(appdata, "Microsoft", "Teams")
        if os.path.isdir(old_teams):
            shutil.rmtree(old_teams, ignore_errors=True)
            teams_cleaned += 1
            log("  삭제: Classic Teams 데이터", -1)

        # New Teams (UWP 패키지)
        for pkg in glob.glob(os.path.join(local, "Packages", "MSTeams_*")):
            shutil.rmtree(pkg, ignore_errors=True)
            teams_cleaned += 1
            log(f"  삭제: {os.path.basename(pkg)}", -1)

        # Teams 추가 캐시 (%LOCALAPPDATA%)
        for name in ["Teams", "TeamsMeetingAddin", "TeamsPresenceAddin"]:
            path = os.path.join(local, "Microsoft", name)
            if os.path.isdir(path):
                shutil.rmtree(path, ignore_errors=True)
                teams_cleaned += 1
                log(f"  삭제: {name}", -1)

        log(f"Teams {teams_cleaned}개 경로 정리 완료", 8)

        # ── [9/9] WAM 검증 + 자동 복구 ──
        wam_ok = True
        for wk in _WAM_KEYS:
            ps = f"if (Test-Path '{wk['path']}') {{ Write-Output 'OK' }} else {{ Write-Output 'MISSING' }}"
            code, out = self._run_ps(ps, log, timeout=10)
            key_name = wk["file"].replace(".reg", "")

            if "MISSING" in out:
                log(f"  [!!] {key_name} 키 누락 — 백업에서 복구 시도", -1)
                backup_file = os.path.join(backup_dir, wk["file"])
                if os.path.isfile(backup_file):
                    self._run_ps(
                        f"reg import '{backup_file}' 2>&1 | Out-Null; "
                        f"if (Test-Path '{wk['path']}') {{ Write-Output 'RESTORED' }} "
                        f"else {{ Write-Output 'FAIL' }}",
                        log, timeout=10,
                    )
                    log(f"  [복구] {key_name}", -1)
                else:
                    # 백업도 없으면 빈 키라도 생성
                    self._run_ps(
                        f"New-Item '{wk['path']}' -Force | Out-Null",
                        log, timeout=10,
                    )
                    log(f"  [최소 복구] {key_name} 빈 키 생성", -1)
                # 재확인
                code2, out2 = self._run_ps(
                    f"if (Test-Path '{wk['path']}') {{ Write-Output 'OK' }} else {{ Write-Output 'FAIL' }}",
                    log, timeout=10,
                )
                if "FAIL" in out2:
                    wam_ok = False
            else:
                log(f"  [OK] {key_name} 건재", -1)

        if wam_ok:
            log("WAM 검증 완료 — 인프라 정상", 9)
        else:
            log("WAM 검증 완료 — 일부 손상, 재부팅 후 확인 필요", 9)

        log("반드시 PC를 재부팅하세요!", -1)
        log("재부팅 후: Edge→프로필 확인, Teams→새 계정 로그인", -1)
        return True

    # ── 헬퍼 ──

    def _clear_folder_contents(self, path: str) -> int:
        """폴더 내용만 삭제 (폴더 자체는 유지). 삭제 수 반환."""
        count = 0
        for item in os.listdir(path):
            fp = os.path.join(path, item)
            try:
                if os.path.isdir(fp):
                    shutil.rmtree(fp, ignore_errors=True)
                else:
                    os.remove(fp)
                count += 1
            except OSError:
                pass
        return count

    def _force_delete_dir(self, path: str, log):
        """잠긴 파일이 있는 폴더를 최대한 삭제 (긴 경로부터)"""
        try:
            items = []
            for root, dirs, files in os.walk(path):
                for f in files:
                    items.append(os.path.join(root, f))
                for d in dirs:
                    items.append(os.path.join(root, d))
            items.sort(key=len, reverse=True)
            for item in items:
                try:
                    if os.path.isfile(item):
                        os.remove(item)
                    elif os.path.isdir(item):
                        os.rmdir(item)
                except OSError:
                    pass
        except OSError:
            pass
