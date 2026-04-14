"""⑫ 입력기 복구 (이전 IME + 한컴 입력기 제거)"""

from tools.base import BaseTool


class ImeFixTool(BaseTool):
    tool_id = "ime_fix"
    name = "입력기 복구"
    requires_admin = False  # HKCU 레지스트리만 수정
    requires_reboot = False

    def get_steps(self):
        return ["한컴 입력기 확인/제거", "이전 버전 IME 전환"]

    def run(self, log):
        # Step 0: 한컴 입력기 제거
        ps_script = (
            "$list = Get-WinUserLanguageList; "
            "$changed = $false; "
            "foreach ($lang in $list) { "
            "  $tips = $lang.InputMethodTips | "
            "    Where-Object { $_ -notlike '*Hancom*' -and $_ -notlike '*0412:A0000012*' }; "
            "  if ($tips.Count -ne $lang.InputMethodTips.Count) { "
            "    $lang.InputMethodTips.Clear(); "
            "    foreach ($tip in $tips) { $lang.InputMethodTips.Add($tip) }; "
            "    $changed = $true "
            "  } "
            "}; "
            "if ($changed) { "
            "  Set-WinUserLanguageList $list -Force; "
            "  Write-Output 'REMOVED' "
            "} else { "
            "  Write-Output 'NOT_FOUND' "
            "}"
        )
        code, output = self._run_ps(ps_script, log, timeout=15)
        if "REMOVED" in output:
            log("한컴 입력기 제거 완료", 0)
        else:
            log("한컴 입력기 없음 (이미 제거됨)", 0)

        # Step 1: 이전 버전 IME 활성화
        import winreg
        key_path = r"SOFTWARE\Microsoft\Input\Settings"
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, key_path, 0,
                winreg.KEY_SET_VALUE | winreg.KEY_CREATE_SUB_KEY,
            )
            winreg.SetValueEx(key, "EnableOldIME", 0, winreg.REG_DWORD, 1)
            winreg.CloseKey(key)
            log("이전 버전 IME 활성화 완료", 1)
        except Exception as e:
            log(f"IME 설정 실패: {e}", -1)
            return False

        return True
