"""도구 레지스트리 — tool_id → BaseTool 클래스 매핑"""

from tools.base import BaseTool
from tools.printer_spooler import PrinterSpoolerTool
from tools.winupdate_cache import WinUpdateCacheTool
from tools.browser_reset import BrowserResetTool
from tools.dns_flush import DnsFlushTool
from tools.network_reset import NetworkResetTool
from tools.temp_cleanup import TempCleanupTool
from tools.explorer_restart import ExplorerRestartTool
from tools.store_app_reset import StoreAppResetTool
from tools.icon_cache import IconCacheTool
from tools.sfc_scan import SfcScanTool
from tools.remote_support import RemoteSupportTool
from tools.ime_fix import ImeFixTool
from tools.ms_account_cleanup import MsAccountCleanupTool
from tools.teams_reinstall import TeamsReinstallTool
from tools.his_reinstall import HisReinstallTool
from tools.banking_reset import BankingResetTool

TOOL_REGISTRY: dict[str, type[BaseTool]] = {
    "printer_spooler": PrinterSpoolerTool,
    "winupdate_cache": WinUpdateCacheTool,
    "browser_reset": BrowserResetTool,
    "dns_flush": DnsFlushTool,
    "network_reset": NetworkResetTool,
    "temp_cleanup": TempCleanupTool,
    "explorer_restart": ExplorerRestartTool,
    "store_app_reset": StoreAppResetTool,
    "icon_cache": IconCacheTool,
    "sfc_scan": SfcScanTool,
    "remote_support": RemoteSupportTool,
    "ime_fix": ImeFixTool,
    "ms_account_cleanup": MsAccountCleanupTool,
    "teams_reinstall": TeamsReinstallTool,
    "his_reinstall": HisReinstallTool,
    "banking_reset": BankingResetTool,
}


def get_tool(tool_id: str) -> BaseTool | None:
    """tool_id로 도구 인스턴스 생성"""
    cls = TOOL_REGISTRY.get(tool_id)
    return cls() if cls else None
