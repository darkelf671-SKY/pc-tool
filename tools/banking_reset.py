"""⑯ 인터넷뱅킹/관공서 보안프로그램 일괄 삭제 + 브라우저 완전 초기화"""

import os
import shutil
import subprocess
import time
from tools.base import BaseTool


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
            "브라우저 완전 초기화",
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
            code = self._run_uninstall(uninstall_cmd, log)
            if code == 0:
                success += 1
            else:
                fail += 1

        log(f"삭제 완료: 성공 {success}개, 실패 {fail}개", 2)
        if fail > 0:
            log("실패한 프로그램은 제어판 > 프로그램 제거에서 수동 삭제하세요", -1)

        # Step 3: 브라우저 완전 초기화 (User Data 폴더 통째 삭제)
        # 캐시/쿠키만 삭제로는 보안프로그램 꼬임이 해결 안 됨 → 완전 초기화 필요
        local = os.environ.get("LOCALAPPDATA", "")
        reset_results = []

        for name, proc, path in [
            ("Edge", "msedge.exe", os.path.join(local, "Microsoft", "Edge", "User Data")),
            ("Chrome", "chrome.exe", os.path.join(local, "Google", "Chrome", "User Data")),
        ]:
            if not os.path.isdir(path):
                reset_results.append(f"{name}: 미설치")
                continue
            # 프로세스 재확인 (Step 0에서 이미 종료했지만 재시작될 수 있음)
            self._run_cmd(f"taskkill /F /IM {proc}", log, timeout=5)
            time.sleep(1)
            shutil.rmtree(path, ignore_errors=True)
            if not os.path.isdir(path):
                reset_results.append(f"{name}: 완전 초기화")
            else:
                # 잠긴 파일 강제 삭제 시도
                self._force_delete_dir(path)
                reset_results.append(f"{name}: 부분 초기화 (재부팅 후 완료)")

        log(f"브라우저 완전 초기화 완료 ({', '.join(reset_results)})", 3)
        log("재부팅 후 은행/관공서 사이트에 접속하면 보안프로그램이 새로 설치됩니다", -1)
        log("브라우저 북마크/저장 비밀번호가 초기화됩니다", -1)
        return True

    def _parse_uninstall_cmd(self, raw: str) -> tuple[str, str]:
        """UninstallString을 (실행파일경로, 나머지인자)로 분리.

        예: '"C:\\Program Files\\app\\un.exe" /arg' → ('"C:\\...\\un.exe"', '/arg')
            'C:\\app\\un.exe /S'                   → ('C:\\app\\un.exe', '/S')
        """
        raw = raw.strip()
        if raw.startswith('"'):
            # 따옴표로 시작 → 닫는 따옴표까지가 실행파일
            end = raw.find('"', 1)
            if end != -1:
                return raw[:end + 1], raw[end + 1:].strip()
            return raw, ""
        # 따옴표 없음 → .exe 뒤에서 분리
        lower = raw.lower()
        for ext in [".exe", ".msi"]:
            idx = lower.find(ext)
            if idx != -1:
                split_at = idx + len(ext)
                return raw[:split_at], raw[split_at:].strip()
        return raw, ""

    def _quote_exe(self, path: str) -> str:
        """공백이 있는 경로에 따옴표 추가 (이미 있으면 그대로)"""
        if path.startswith('"'):
            return path
        if " " in path:
            return f'"{path}"'
        return path

    def _run_uninstall(self, uninstall_cmd: str, log) -> int:
        """언인스톨 명령 실행 (MsiExec/일반 자동 판별, 사일런트 플래그 다중 시도)"""
        # MsiExec 기반
        if "msiexec" in uninstall_cmd.lower():
            cmd = uninstall_cmd.replace("/I", "/X").replace("/i", "/X")
            if "/quiet" not in cmd.lower() and "/qn" not in cmd.lower():
                cmd += " /quiet /norestart"
            code, _ = self._run_cmd(cmd, log, timeout=120)
            return code

        # 일반 언인스톨러 — 실행파일과 인자 분리 + 경로 따옴표 처리
        exe_path, existing_args = self._parse_uninstall_cmd(uninstall_cmd)
        exe_quoted = self._quote_exe(exe_path)

        # 이미 사일런트 플래그가 있으면 그대로 실행
        lower_args = existing_args.lower()
        if any(f in lower_args for f in ["/s", "/silent", "/verysilent", "/qn", "-s"]):
            cmd = f"{exe_quoted} {existing_args}".strip()
            code, _ = self._run_cmd(cmd, log, timeout=120)
            return code

        # 사일런트 플래그 다중 시도 (NSIS→InnoSetup→InstallShield)
        # 짧은 timeout으로 시도 (GUI 팝업되면 빠르게 다음으로)
        silent_flags = ["/S", "/silent", "/VERYSILENT", "/qn", "-s"]
        code = -1
        for flag in silent_flags:
            cmd = f"{exe_quoted} {existing_args} {flag}".strip()
            code, _ = self._run_cmd(cmd, log, timeout=30)
            if code == 0:
                return 0

        return code

    def _force_delete_dir(self, path: str):
        """잠긴 파일이 있는 폴더를 최대한 삭제"""
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
