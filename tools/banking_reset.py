"""⑯ 인터넷뱅킹/관공서 보안프로그램 일괄 삭제 + 브라우저 데이터 정리"""

import os
import subprocess
import time
from tools.base import BaseTool
from tools.browser_reset import BrowserResetTool


# 탐지 패턴 (DisplayName 부분 일치, 대소문자 무시)
# 카테고리: keyboard=키보드보안, cert=인증/전자서명, firewall=방화벽/해킹방지,
#           installer=통합설치, ip=IP탐지, etc=기타
_SECURITY_PATTERNS = [
    # ── 키보드 보안 (키로거 방지) ──
    "TouchEn nxKey",
    "TouchEn PC",
    "TouchEn Key",
    "Touchenex",
    "KeySharp",
    "nProtect KeyCrypt",
    "Interezen",
    "UniCRSv",
    "Softcamp Secure KeyStroke",
    "Softcamp SecureKeystroke",
    "SoftCamp Client",
    "Raonsecure",
    "K-Defense",
    # ── 인증서 / 전자서명 / PKI ──
    "INISAFE CrossWeb",
    "INISAFE Web",
    "INISAFE SFilter",
    "INISAFE EX",
    "INISAFEWeb",
    "INITECH CrossWebEX",
    "INITECH INISAFE",
    "XecureWeb",
    "XecureSmart",
    "MagicLine",
    "MAGIC LINE",
    "MAGIC PKI",
    "AnySign",
    "AnySign4PC",
    "AnySign_Installer",
    "CrossCert",
    "SignKorea",
    "KOSCOM Sign",
    "yessign",
    "NOS ",
    "ClientKeeper",
    "SignGate",
    "SafeIdentity",
    "TradeSign",
    "NeoSign",
    "UniSign",
    # ── 통합설치 관리자 ──
    "WIZVERA Delfino",
    "WIZVERA Process Manager",
    "Wizvera Veraport",
    "Delfino G3",
    "Veraport",
    "VeraPort",
    # ── 방화벽 / 해킹방지 / 백신 ──
    "AhnLab Safe Transaction",
    "AhnLab Online Security",
    "AOS(",
    "ASTx",
    "nProtect Online Security",
    "nProtect Netizen",
    "nProtect Browser",
    "TrustGuard",
    "Trusteer Rapport",
    "Websign",
    "Safe Webcard",
    # ── IP 탐지 / PC 정보 수집 ──
    "IPinside",
    "IPinsideAgent",
    "IPinside LWS",
    "IPinside_LWS",
    "InfoOcean",
    # ── 관공서 / 공공기관 (정부24, 홈택스, 나라장터, 위택스 등) ──
    "GPKI",
    "GreatGPKI",
    "GPKI Web Client",
    "GPKI Certification",
    "EPKI",
    "Government Plugin",
    "GovPass",
    "HancomGMD",
    "Hancom GMD",
    "HANCOM GMD Secure",
    "Hancom Secure",
    "KSIGN",
    "KSignSecure",
    "NaraSign",
    "SecureGate",
    "SGA-PKI",
    "SGA Solutions",
    "UniTrust",
    "UniFinger",
    "KICA",
    "EncTek",
    "SoftForum",
    "Dream Security",
    "Dreamsecurity",
    "JCE_for_Java",
    "NxClient",
    "ISSAC",
    # ── 기타 금융/공공 보안 ──
    "MarkAny",
    "MarkAny e-Page",
    "MarkAny MaI",
    "Fasoo DRM",
    "KCaseAgent",
    "ObzerAgent",
    "SECUI MF2",
    "Ananti",
    "ezCertManager",
    "ezGuard",
    "CRISION",
    "Smart Security",
    "SecureWeb",
    "KoreaEXE",
    "AxECM",
    "AxLocker",
    "SafeNet Authentication",
]

# 관련 프로세스 (삭제 전 강제 종료)
_SECURITY_PROCESSES = [
    "TouchEn",
    "Touchenex",
    "KeySharp",
    "nProtect",
    "CrossWeb",
    "MagicLine",
    "MAGIC",
    "AnySign",
    "Delfino",
    "Veraport",
    "VeraPort",
    "IPinside",
    "ASTx",
    "SafeTransaction",
    "AhnLabSafe",
    "NOS ",
    "ClientKeeper",
    "INISAFE",
    "INITECH",
    "XecureWeb",
    "XecureSmart",
    "GPKI",
    "SoftForum",
    "KSIGN",
    "HancomGMD",
    "NxClient",
    "SignGate",
    "Dreamsecurity",
    "Trusteer",
    "MarkAny",
]


class BankingResetTool(BaseTool):
    tool_id = "banking_reset"
    name = "보안프로그램 초기화 (뱅킹/관공서)"
    requires_admin = True
    requires_reboot = True

    def get_steps(self):
        return [
            "보안프로그램 프로세스 종료",
            "설치된 보안프로그램 탐지",
            "보안프로그램 일괄 삭제",
            "브라우저 데이터 정리",
        ]

    def run(self, log):
        # Step 0: 관련 프로세스 강제 종료
        killed = 0
        for pattern in _SECURITY_PROCESSES:
            code, output = self._run_ps(
                f"Get-Process | Where-Object {{ $_.ProcessName -like '*{pattern}*' }} | "
                f"Stop-Process -Force -ErrorAction SilentlyContinue",
                log, timeout=10,
            )
            if code == 0:
                killed += 1
        # 브라우저도 종료 (보안프로그램이 브라우저에 연결됨)
        for proc in ["msedge.exe", "chrome.exe", "iexplore.exe"]:
            self._run_cmd(f"taskkill /F /IM {proc}", log, timeout=5)
        time.sleep(1)
        log(f"보안프로그램 및 브라우저 프로세스 종료", 0)

        # Step 1: 설치된 보안프로그램 탐지
        found = self._detect_installed(log)
        if not found:
            log("설치된 보안프로그램을 찾을 수 없습니다", 1)
            log("이미 삭제되었거나 탐지 범위에 없는 프로그램일 수 있습니다", -1)
            return True

        log(f"보안프로그램 {len(found)}개 탐지됨:", 1)
        for item in found:
            log(f"  • {item['name']}", -1)

        # Step 2: 일괄 삭제
        success = 0
        fail = 0
        for item in found:
            uninstall_cmd = item.get("uninstall", "")
            if not uninstall_cmd:
                fail += 1
                continue

            log(f"  삭제 중: {item['name']}", -1)
            # MsiExec 기반
            if "MsiExec" in uninstall_cmd or "msiexec" in uninstall_cmd:
                # /I를 /X로, 사일런트 옵션 추가
                cmd = uninstall_cmd.replace("/I", "/X")
                if "/quiet" not in cmd.lower() and "/qn" not in cmd.lower():
                    cmd += " /quiet /norestart"
                code, _ = self._run_cmd(cmd, log, timeout=60)
            else:
                # 일반 언인스톨러
                # 사일런트 옵션 시도
                cmd = uninstall_cmd
                if "/S" not in cmd and "/silent" not in cmd.lower():
                    cmd += " /S"
                code, _ = self._run_cmd(f'"{cmd}"' if " " in cmd and '"' not in cmd else cmd, log, timeout=60)

            if code == 0:
                success += 1
            else:
                fail += 1

        log(f"삭제 완료: 성공 {success}개, 실패 {fail}개", 2)
        if fail > 0:
            log("실패한 프로그램은 제어판 > 프로그램 제거에서 수동 삭제하세요", -1)

        # Step 3: 브라우저 데이터 정리 (캐시/쿠키 — 재설치 무한루프 방지)
        local = os.environ.get("LOCALAPPDATA", "")
        browser_tool = BrowserResetTool()
        edge_profile = os.path.join(local, r"Microsoft\Edge\User Data\Default")
        edge_cnt = browser_tool._clear_browser_data(edge_profile)
        chrome_profile = os.path.join(local, r"Google\Chrome\User Data\Default")
        chrome_cnt = browser_tool._clear_browser_data(chrome_profile)
        log(f"브라우저 데이터 정리 완료 (Edge {edge_cnt}개 + Chrome {chrome_cnt}개 항목 삭제)", 3)
        log("재부팅 후 은행/관공서 사이트에 접속하면 보안프로그램이 새로 설치됩니다", -1)
        return True

    def _detect_installed(self, log) -> list[dict]:
        """레지스트리에서 설치된 보안프로그램 탐지"""
        ps_script = (
            "$results = @(); "
            "$paths = @("
            "'HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\*',"
            "'HKLM:\\SOFTWARE\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\*',"
            "'HKCU:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\*'"
            "); "
            "foreach ($p in $paths) { "
            "  Get-ItemProperty $p -ErrorAction SilentlyContinue | "
            "  Where-Object { $_.DisplayName } | "
            "  ForEach-Object { "
            "    $results += [PSCustomObject]@{ "
            "      Name = $_.DisplayName; "
            "      Uninstall = $_.UninstallString; "
            "      Quiet = $_.QuietUninstallString; "
            "    } "
            "  } "
            "}; "
            "$results | ConvertTo-Json -Compress"
        )
        code, output = self._run_ps(ps_script, log, timeout=15)

        if code != 0 or not output.strip():
            return []

        import json
        try:
            # PowerShell 출력에서 JSON 부분만 추출
            json_str = output.strip()
            # 단일 객체면 리스트로 감싸기
            if json_str.startswith("{"):
                json_str = f"[{json_str}]"
            all_programs = json.loads(json_str)
        except (json.JSONDecodeError, ValueError):
            return []

        # 패턴 매칭
        found = []
        seen_names = set()
        for prog in all_programs:
            name = prog.get("Name", "")
            if not name or name in seen_names:
                continue
            name_lower = name.lower()
            for pattern in _SECURITY_PATTERNS:
                if pattern.lower() in name_lower:
                    uninstall = prog.get("Quiet") or prog.get("Uninstall") or ""
                    found.append({
                        "name": name,
                        "uninstall": uninstall,
                    })
                    seen_names.add(name)
                    break

        return found
