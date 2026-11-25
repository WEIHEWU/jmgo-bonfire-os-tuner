#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bonfire OS Tuning Tool for JMGO N5/N5S — cross-platform Python version.
Replaces bonfire_tuner_full.sh and bonfire_tuner_full.bat.
"""

from __future__ import annotations

import os
import re
import select as _select_mod
import shutil
import shlex
import socket
import struct
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

# ---------------------------------------------------------------------------
# Colors
# ---------------------------------------------------------------------------

if sys.platform == "win32":
    # Enable ANSI on Windows 10+
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    except Exception:
        pass

USE_COLOR = sys.stdout.isatty() or os.environ.get("FORCE_COLOR")

def _c(code: str) -> str:
    return code if USE_COLOR else ""

RED    = _c("\033[0;31m")
GREEN  = _c("\033[0;32m")
YELLOW = _c("\033[1;33m")
BLUE   = _c("\033[0;34m")
CYAN   = _c("\033[0;36m")
BOLD   = _c("\033[1m")
DIM    = _c("\033[2m")
NC     = _c("\033[0m")

import builtins as _builtins

_ZH = {
    'Stock JMGO Settings (com.jmgo.setting.x) was not found on the connected device. No APK was installed.': '连接的设备上未找到原厂设置（com.jmgo.setting.x），未安装 APK。',
    '3D activation for the original settings is temporary and is lost after a projector reboot.': '原厂设置中的 3D 激活是临时的，投影仪重启后会失效。',
    'Verify speech with the physical remote; software checks cannot confirm microphone audio.': '请用实体遥控器验证语音；软件检查无法确认麦克风音频。',
    'jmgo.option.video is empty; refusing to replace an unknown device configuration.': 'jmgo.option.video 为空，拒绝替换未知设备配置。',
    'Custom Settings was installed, but required permissions could not be verified': '自定义设置已安装，但无法验证所需权限',
    'The optional bridge opens Google search on MIC (609); enable only if needed.': '可选桥接会在按 MIC（609）时打开 Google 搜索，按需启用。',
    'JMGO Settings Clone installation failed — stock settings were not changed.': 'JMGO 设置克隆版安装失败 — 原厂设置未改动。',
    'Could not determine the current Android user; permissions were not changed': '无法确定当前 Android 用户，权限未改动',
    'In an app: select its microphone icon, then hold MIC, speak and release.': '在应用内点麦克风图标，按住 MIC 说话后松开。',
    'Reopen the original Settings, then open Picture -> Advanced -> 3D Mode.': '重新打开原厂设置，然后进入 图像 → 高级 → 3D 模式。',
    'No apps were disabled — install their replacements first, then re-run.': '未禁用任何应用 — 请先安装替代应用后重试。',
    'Screensaver installation failed — stock screensaver was NOT replaced.': '屏保安装失败 — 原厂屏保未被替换。',
    'N5S: first try native MIC hold-to-talk with Google speech services.': 'N5S：先尝试原生麦克风按键通话 + Google 语音服务。',
    'Could not remove Google TV Screensaver — it may still be installed.': '无法移除 Google TV 屏保 — 可能仍有安装。',
    'ADB not found on known ports. Scanning port range (33000-47000)...': '已知端口未找到 ADB，正在扫描 33000-47000 端口...',
    'Installing JMGO Settings Clone alongside the stock settings app...': '正在与原厂设置并存安装 JMGO 设置克隆版...',
    'Install/configure Google TV Search? Answer No to restore AI Voice': '安装/配置 Google TV 搜索？选“否”恢复 AI 语音',
    'Stock screensaver package (com.jmgo.os.dream) not found on device': '设备上未找到原厂屏保包（com.jmgo.os.dream）',
    'The custom settings clone exposes its 3D menu without this task.': '自定义设置克隆版无需此步骤即可显示 3D 菜单。',
    'is not listed after install — stock settings were not changed.': '安装后未列出 — 原厂设置未改动。',
    'JMGO Settings Clone installed; stock settings remain available': 'JMGO 设置克隆版已安装；原厂设置仍可用',
    'Disable selected Chinese stock apps? Answer No to restore them': '禁用选中的中文预装应用？选“否”恢复',
    'not found after install — stock screensaver was NOT replaced.': '安装后未找到 — 原厂屏保未被替换。',
    'Keeping AI Voice: N5S native MIC handling or unknown model.': '保留 AI 语音：N5S 原生麦克风处理或型号未知。',
    'Bundled adb.exe not found and ADB is not available in PATH': '未找到内置 adb.exe，且 PATH 中没有 ADB',
    'Store install permission verified for all found app stores': '已验证所有找到的应用商店的安装权限',
    'In SmartTube select external microphone for voice search.': '在 SmartTube 中选择外部麦克风进行语音搜索。',
    'Some APK directories are missing. Installation may fail.': '部分 APK 目录缺失，安装可能失败。',
    'Make sure ADB over network is enabled on the projector:': '请确认投影仪已开启网络 ADB：',
    'Screensaver disabled — screen will stay on indefinitely': '屏保已禁用 — 屏幕将一直保持开启',
    'Could not list user apps; permissions were not changed': '无法列出用户应用，权限未改动',
    'Could not disable Voice Bridge after setup failure:': '配置失败后无法关闭语音桥接：',
    'No known app stores found, searching by keywords...': '未找到已知应用商店，正在按关键词搜索...',
    'Temporary 3D menu disabled in the original settings': '原厂设置中的临时 3D 菜单已关闭',
    '3D properties were not accepted by the projector.': '投影仪未接受 3D 属性。',
    'Screen-off timeout (before screensaver starts):': '熄屏超时（屏保启动前）：',
    'Install or update Custom Settings (JMGO Clone)?': '安装/更新自定义设置（JMGO 克隆版）？',
    'Could not determine the voice-search mechanism': '无法确定语音搜索机制',
    'Could not remove the temporary 3D menu option.': '无法移除临时 3D 菜单选项。',
    'No device connected. Please check connection.': '未连接设备，请检查连接。',
    'Settings → About → Build Number (tap 7 times)': '设置 → 关于 → 版本号（连点 7 次）',
    'Could not verify Google microphone permission': '无法验证 Google 麦克风权限',
    'Stock AI Voice is still installed for user 0': '原厂 AI 语音仍安装在该用户下',
    'Could not verify Google overlay permission': '无法验证 Google 悬浮窗权限',
    'Google TV Screensaver configured (timeout:': 'Google TV 屏保已配置（超时：',
    'Developer Options → ADB over network → ON': '开发者选项 → 网络 ADB → 开启',
    'AmbientMode.apk not found in screensaver/': 'screensaver/ 中未找到 AmbientMode.apk',
    'some General settings may not be applied.': '部分常规设置可能无法生效。',
    'Enable 3D menu in the original settings?': '在原厂设置中启用 3D 菜单？',
    '3D menu enabled in the original settings': '原厂设置中的 3D 菜单已启用',
    'Pushing port configuration to device...': '正在向设备写入端口配置...',
    'Fixing app store install permissions...': '正在修复应用商店安装权限...',
    'package is still unavailable for user 0': '该用户下仍不可用',
    'Please install Android Platform Tools:': '请安装 Android Platform Tools：',
    'Developer Options → USB Debugging → ON': '开发者选项 → USB 调试 → 开启',
    'Bonfire OS Tuning Tool N5/N5S Edition': 'Bonfire OS 调校工具 N5/N5S 版',
    'Disable or Restore Chinese Stock Apps': '禁用/恢复中文预装应用',
    'Enable the optional N5S Voice Bridge?': '启用可选的 N5S 语音桥接？',
    'Voice-search setup was not completed:': '语音搜索配置未完成：',
    'Install Custom Settings (JMGO Clone)': '安装自定义设置（JMGO 克隆版）',
    'Installing Google TV Screensaver...': '正在安装 Google TV 屏保...',
    'Disabling screensaver completely...': '正在完全禁用屏保...',
    'Restoring stock JMGO screensaver...': '正在恢复 JMGO 原厂屏保...',
    'Reenabling JMGO update services...': '正在恢复 JMGO 更新服务...',
    'Port (leave empty for auto-detect': '端口（留空自动检测',
    'Australia/Sydney timezone applied': '已应用澳大利亚/悉尼时区',
    'Removing Google TV Screensaver...': '正在移除 Google TV 屏保...',
    'Stock apps reenabled and verified': '原厂应用已恢复并验证',
    'Disabling JMGO update services...': '正在关闭 JMGO 更新服务...',
    'Press Enter to return to menu...': '按回车返回菜单...',
    'Apply Australia/Sydney timezone?': '应用澳大利亚/悉尼时区？',
    'RU addons installation completed': 'RU 插件包安装完成',
    'User apps installation completed': '用户应用安装完成',
    'Apply Australia/Sydney timezone': '应用澳大利亚/悉尼时区',
    'N5S speech providers configured': '已配置 N5S 语音服务',
    'Stock AI Voice was not disabled': '原厂 AI 语音未被禁用',
    'Stock JMGO screensaver restored': 'JMGO 原厂屏保已恢复',
    'Fixing user apps permissions...': '正在修复用户应用权限...',
    'Waiting for device to be ready': '等待设备就绪',
    'directory not found — skipping': '目录未找到 — 跳过',
    'Disable screensaver completely': '完全禁用屏保',
    'Restore stock JMGO screensaver': '恢复 JMGO 原厂屏保',
    'app(s); see the reasons above.': '个应用；见上方原因。',
    'Device not ready, retrying...': '设备未就绪，重试中...',
    "type 'a' to force auto-detect": '输入 a 强制自动检测',
    'Invalid choice, using default': '选择无效，使用默认值',
    'Install Google TV Screensaver': '安装 Google TV 屏保',
    'No app stores found on device': '设备上未找到应用商店',
    'Install User Apps (userpack)': '安装用户应用（userpack）',
    'OK, skipping permissions fix': '好的，跳过权限修复',
    'user apps; unconfirmed apps:': '个用户应用；未确认的应用：',
    'Permissions verified for all': '已验证所有',
    'Scanning known ADB ports on': '正在扫描已知 ADB 端口',
    'Could not find ADB port on': '未找到 ADB 端口：',
    'Google TV Search installed': 'Google TV 搜索已安装',
    'Some Chinese apps disabled': '部分中文应用已禁用',
    'Fix User Apps Permissions?': '修复用户应用权限？',
    'JMGO OTA updates reenabled': 'JMGO OTA 更新已恢复',
    'Fix User Apps Permissions': '修复用户应用权限',
    'Fix App Store Permissions': '修复应用商店权限',
    'Provider rollback failed:': '语音服务回退失败：',
    'Disabling Chinese apps...': '正在禁用中文应用...',
    'Disable JMGO OTA updates?': '关闭 JMGO OTA 更新？',
    'JMGO OTA updates disabled': 'JMGO OTA 更新已关闭',
    'Install Google TV Search': '安装 Google TV 搜索',
    'Disable JMGO OTA Updates': '关闭 JMGO OTA 更新',
    'Reenabling stock apps...': '正在恢复原厂应用...',
    'Permissions verified for': '已验证权限：',
    'File not found: search/': '未找到文件：search/',
    'OK, skipping RU addons': '好的，跳过 RU 插件包',
    'Configure Screensaver': '设置屏保',
    'ADB not found in PATH': 'PATH 中没有 ADB',
    'Chinese apps disabled': '中文应用已禁用',
    'Missing search APKs:': '缺少搜索 APK：',
    'Voice Bridge enabled': '语音桥接已启用',
    'Screensaver options:': '屏保选项：',
    'Failed to connect to': '连接失败：',
    'All done! Have fun!': '全部完成！',
    'Timezone set to GMT': '时区已设为 GMT',
    'Voice-search setup:': '语音搜索方案：',
    'Using the universal': '使用通用版',
    'Rebooting device...': '正在重启设备...',
    'Reboot command sent': '重启指令已发送',
    'Enable 3D Settings': '开启 3D 设置',
    'No user apps found': '未找到用户应用',
    'Reboot Bonfire OS?': '重启 Bonfire OS？',
    'Select an action:': '请选择操作：',
    'Install RU Addons': '安装 RU 插件包',
    'Reboot Bonfire OS': '重启 Bonfire OS',
    'ADB found on port': '已在端口找到 ADB',
    'Type IP of device': '输入设备 IP',
    'Invalid IP format': 'IP 格式无效',
    'Invalid argument:': '参数无效：',
    'Failed to install': '安装失败：',
    'AI Voice restored': 'AI 语音已恢复',
    'Could not restore': '无法恢复',
    'Device connected': '设备已连接',
    'connect directly': '直接连接',
    'auto-detect port': '自动检测端口',
    'interactive mode': '交互模式',
    'Continue anyway?': '仍要继续吗？',
    'No APKs found in': '未找到 APK：',
    'No changes made.': '未做任何更改。',
    'No changes made': '未做任何更改',
    'native MIC mode': '原生麦克风模式',
    'Choose timeout': '选择超时',
    'Invalid choice': '选择无效',
    'Could not save': '无法保存',
    'Connecting to': '正在连接',
    'connecting...': '正在连接...',
    'Choose option': '选择选项',
    'Enter to skip': '回车跳过',
    'OK, no reboot': '好的，不重启',
    'sequentially': '依次',
    'Connected to': '已连接至',
    "Directory '": "目录 '",
    "' not found": "' 未找到",
    'APK(s) from': '个 APK，来自',
    'Interrupted': '已中断',
    'Installing': '正在安装',
    ', A, or Q.': '、A 或 Q。',
    '[WARNING]': '[警告]',
    '[Yes/No]': '[是/否]',
    '[yes/No]': '[是/否]',
    'default:': '默认：',
    'Skipping': '跳过',
    'Restored': '已恢复',
    '[ERROR]': '[错误]',
    'Run ALL': '全部执行',
    'Choice:': '选择：',
    'on port': '端口',
    'Skipped': '已跳过',
    '[INFO]': '[信息]',
    'Usage:': '用法：',
    'Done:': '完成：',
    '[OK]': '[成功]',
    'Quit': '退出',
    'Bye!': '再见！',
    'stock settings': '原厂设置版本',
    'model': '型号',
    'menu item': '菜单项',
    'Google TV Search': 'Google TV 搜索',
    'Google TV Screensaver': 'Google TV 屏保',
    'Voice Bridge': '语音桥接',
    'AI Voice': 'AI 语音',
    'Custom Settings': '自定义设置',
    'JMGO Clone': 'JMGO 克隆版',
    'stock apps': '原厂应用',
    'Chinese apps': '中文应用',
    'user apps': '用户应用',
    'app store(s)': '应用商店',
    'app stores': '应用商店',
    'Automatic time zone disabled to keep the setting': '已关闭自动时区，防止设置被覆盖',
    'Automatic time zone reenabled': '自动时区已重新开启',
    'Google TV Search installed with voice bridge': 'Google TV 搜索与语音桥接已安装',
    'In an app: select its microphone icon, then hold MIC, speak and release.': '在应用中：点麦克风图标，然后长按 MIC 说话后松开。',
    'Settings button interception enabled. To make the SETTINGS key open the clone, go to General > Remote keys > Settings and bind Short press to Full menu (one-time, stored in app preferences).': '设置键拦截已启用。要让设置键打开克隆版，请进入 通用 > 遥控器按键 > 设置，把短按绑定为完整菜单（一次性设置，保存在应用偏好中）。',
    'Screen mirroring ({}) is kept enabled.': '投屏（{}）已保持启用。',
    'Screen mirroring restored: {}': '投屏已恢复：{}',
}

def _zh_text(s: str) -> str:
    if not isinstance(s, str):
        return s
    for en, zh in _ZH.items():
        s = s.replace(en, zh)
    return s

_orig_print = _builtins.print
def _zh_print(*args, **kwargs):
    return _orig_print(*(_zh_text(a) for a in args), **kwargs)
_builtins.print = _zh_print

_orig_input = _builtins.input
def _zh_input(prompt=""):
    return _orig_input(_zh_text(prompt))
_builtins.input = _zh_input


SCRIPT_DIR = Path(__file__).resolve().parent
CONNECTION_FILE = SCRIPT_DIR / ".adb_last_connection"
TOOL_VERSION = "2026.09.12-au-sydney"

# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------

def print_status(msg: str)  -> None: print(f"{GREEN}[OK]{NC} {msg}")
def print_error(msg: str)   -> None: print(f"{RED}[ERROR]{NC} {msg}")
def print_warning(msg: str) -> None: print(f"{YELLOW}[WARNING]{NC} {msg}")
def print_info(msg: str)    -> None: print(f"{BLUE}[INFO]{NC} {msg}")

def clear_screen() -> None:
    os.system("cls" if sys.platform == "win32" else "clear")

def print_header() -> None:
    clear_screen()
    print(f"{BOLD}============================================{NC}")
    print(f"{BOLD}  Bonfire OS Tuning Tool N5/N5S Edition  {NC}")
    print(f"{BOLD}                 {TOOL_VERSION}                 {NC}")
    print(f"{BOLD}============================================{NC}\n")

def prompt_yes_no(question: str, default: str = "Y") -> bool:
    if default.upper() == "Y":
        suffix = f"[{GREEN}Y{NC}es/{RED}N{NC}o]"
        default_yes = True
    else:
        suffix = f"[{RED}Y{NC}es/{GREEN}N{NC}o]"
        default_yes = False
    try:
        resp = input(f"{question} {BLUE}[INPUT]{NC} {suffix} ").strip()
    except EOFError:
        return default_yes
    if not resp:
        return default_yes
    return resp.lower().startswith("y")

def press_enter(msg: str = "Press Enter to return to menu...") -> None:
    try:
        input(msg)
    except EOFError:
        pass

# ---------------------------------------------------------------------------
# ADB wrapper
# ---------------------------------------------------------------------------

def _find_adb_executable() -> str | None:
    """Prefer the bundled Windows ADB, otherwise use ADB from PATH."""
    if sys.platform == "win32":
        bundled_adb = SCRIPT_DIR / "adb.exe"
        if bundled_adb.is_file():
            return str(bundled_adb)
    return shutil.which("adb")


ADB_EXECUTABLE = _find_adb_executable()
ACTIVE_DEVICE_SERIAL: str | None = None


def check_adb() -> None:
    if ADB_EXECUTABLE is None:
        if sys.platform == "win32":
            print_error("Bundled adb.exe not found and ADB is not available in PATH")
        else:
            print_error("ADB not found in PATH")
        print("Please install Android Platform Tools:")
        print("  - macOS:   brew install android-platform-tools")
        print("  - Linux:   sudo apt install adb (or equivalent)")
        print("  - Windows: https://developer.android.com/tools/releases/platform-tools")
        sys.exit(1)

def adb(*args: str, check: bool = False, timeout: int | None = None) -> subprocess.CompletedProcess:
    """Run adb with given args. Always captures stdout/stderr."""
    if ADB_EXECUTABLE is None:
        raise RuntimeError("ADB executable is not available")
    cmd = [ADB_EXECUTABLE, *args]
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=check,
    )


def adb_device(*args: str, check: bool = False, timeout: int | None = None) -> subprocess.CompletedProcess:
    """Run an ADB command against the projector selected by the tuner."""
    if ACTIVE_DEVICE_SERIAL is None:
        raise RuntimeError("ADB target device is not selected")
    return adb("-s", ACTIVE_DEVICE_SERIAL, *args, check=check, timeout=timeout)


def adb_shell(cmd: str) -> subprocess.CompletedProcess:
    return adb_device("shell", cmd)

def adb_install_apk(
    apk_path: Path, *, timeout: int = 300, allow_downgrade: bool = False
) -> bool:
    """Install an APK and return True only on confirmed success."""
    install_args = ["install", "-r", "-g"]
    if allow_downgrade:
        install_args.append("-d")
    res = adb_device(*install_args, str(apk_path), timeout=timeout)
    out = ((res.stdout or "") + (res.stderr or "")).strip()
    if res.returncode != 0 or "Failure" in out or "Error" in out:
        if out:
            print_error(out)
        return False
    return True

def package_installed(pkg: str) -> bool:
    """Return True if *pkg* is installed on the device."""
    pkgs = adb_shell(f"pm list packages {pkg}").stdout or ""
    return f"package:{pkg}" in pkgs.splitlines()

def restore_existing_package(pkg: str) -> bool:
    """Restore a system package for user 0 and verify that it is visible again."""
    result = adb_shell(f"cmd package install-existing --user 0 {pkg}")
    adb_shell(f"pm enable --user 0 {pkg}")
    if package_installed(pkg):
        return True

    output = ((result.stdout or "") + (result.stderr or "")).strip()
    if output:
        print_warning(f"Could not restore {pkg}: {output}")
    else:
        print_warning(f"Could not restore {pkg}: package is still unavailable for user 0")
    return False

def adb_devices_connected() -> bool:
    try:
        out = adb("devices", timeout=10).stdout
    except subprocess.TimeoutExpired:
        return False
    for line in out.splitlines()[1:]:
        columns = line.strip().split()
        if len(columns) < 2 or columns[1] != "device":
            continue
        if ACTIVE_DEVICE_SERIAL is None or columns[0] == ACTIVE_DEVICE_SERIAL:
            return True
    return False

def wait_for_device(max_attempts: int = 3) -> None:
    for attempt in range(1, max_attempts + 1):
        print_info(f"Waiting for device to be ready (attempt {attempt}/{max_attempts})...")
        try:
            if ACTIVE_DEVICE_SERIAL is None:
                adb("wait-for-device", timeout=5)
            else:
                adb_device("wait-for-device", timeout=5)
        except subprocess.TimeoutExpired:
            pass
        if adb_devices_connected():
            time.sleep(1)
            return
        if attempt < max_attempts:
            print_warning("Device not ready, retrying...")

def check_connection() -> None:
    if not adb_devices_connected():
        print_error("No device connected. Please check connection.")
        sys.exit(1)
    print_status("Device connected")

def save_connection(ip: str, port: str | int) -> None:
    CONNECTION_FILE.write_text(f'default_ip="{ip}"\ndefault_port="{port}"\n', encoding="utf-8")

def load_connection() -> tuple[str, str]:
    if not CONNECTION_FILE.exists():
        return "", ""
    ip = port = ""
    try:
        for line in CONNECTION_FILE.read_text(encoding="utf-8").splitlines():
            m = re.match(r'(\w+)="([^"]*)"', line.strip())
            if not m:
                continue
            key, val = m.group(1), m.group(2)
            if key == "default_ip":
                ip = val
            elif key == "default_port":
                port = val
    except OSError:
        pass
    return ip, port

# ---------------------------------------------------------------------------
# Port discovery
# ---------------------------------------------------------------------------

def adb_probe(ip: str, port: int, timeout: float = 1.5) -> bool:
    """Check if port runs an ADB daemon via protocol handshake (no subprocess)."""
    ADB_CNXN = 0x4E584E43   # "CNXN"
    ADB_AUTH = 0x48545541   # "AUTH"
    ADB_STLS = 0x534C5453   # "STLS" — StartTLS (Android 9+)
    try:
        with socket.create_connection((ip, port), timeout=timeout) as s:
            s.settimeout(timeout)
            data = b"host::\x00"
            checksum = sum(data) & 0xFFFFFFFF
            header = struct.pack(
                "<6I",
                ADB_CNXN,
                0x01000000,              # protocol version
                256 * 1024,              # max payload (256 KB)
                len(data),
                checksum,
                ADB_CNXN ^ 0xFFFFFFFF,  # magic
            )
            s.sendall(header + data)
            resp = b""
            while len(resp) < 24:
                chunk = s.recv(24 - len(resp))
                if not chunk:
                    return False
                resp += chunk
            cmd = struct.unpack("<I", resp[:4])[0]
            return cmd in (ADB_CNXN, ADB_AUTH, ADB_STLS)
    except OSError:
        return False

def _tcp_open(ip: str, port: int, timeout: float = 0.15) -> bool:
    """Quick TCP connect check. Reliable on macOS/Linux (not on Windows)."""
    try:
        with socket.create_connection((ip, port), timeout=timeout):
            return True
    except OSError:
        return False

# Pre-built ADB CNXN packet for batch scanner (Windows)
_ADB_CNXN_CMD = 0x4E584E43
_ADB_VALID_CMDS = {0x4E584E43, 0x48545541, 0x534C5453}
_cnxn_data = b"host::\x00"
_cnxn_crc = sum(_cnxn_data) & 0xFFFFFFFF
_CNXN_PKT = struct.pack("<6I", _ADB_CNXN_CMD, 0x01000000, 256 * 1024,
                         len(_cnxn_data), _cnxn_crc,
                         _ADB_CNXN_CMD ^ 0xFFFFFFFF) + _cnxn_data

def _scan_adb_batch_win(ip: str, ports: list[int], ignored: set[int],
                         workers: int = 50, read_timeout: float = 0.5) -> list[int]:
    """Windows: threaded connect+send ADB CNXN, then select for responses."""
    sent: dict[int, socket.socket] = {}

    def _try(p: int) -> tuple[int, socket.socket] | None:
        if p in ignored:
            return None
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER,
                         struct.pack("ii", 1, 0))
            s.settimeout(0.4)
            if s.connect_ex((ip, p)) == 0:
                s.sendall(_CNXN_PKT)
                return (p, s)
            s.close()
        except Exception:
            try:
                s.close()
            except Exception:
                pass
        return None

    with ThreadPoolExecutor(max_workers=workers) as ex:
        for result in ex.map(_try, ports):
            if result:
                p, s = result
                sent[p] = s

    found: list[int] = []
    sent_list = list(sent.values())
    fd_to_port = {s.fileno(): p for p, s in sent.items()}
    for i in range(0, len(sent_list), 450):
        batch = sent_list[i:i + 450]
        for s in batch:
            s.setblocking(False)
        try:
            rl, _, _ = _select_mod.select(batch, [], [], read_timeout)
            for s in rl:
                p = fd_to_port.get(s.fileno())
                try:
                    resp = s.recv(24)
                    if len(resp) >= 4:
                        cmd = struct.unpack("<I", resp[:4])[0]
                        if cmd in _ADB_VALID_CMDS:
                            found.append(p)
                except Exception:
                    pass
        except Exception:
            pass

    for s in sent.values():
        try:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER,
                         struct.pack("ii", 1, 0))
            s.close()
        except Exception:
            pass
    return found

def _scan_adb_batch_unix(ip: str, ports: list[int], ignored: set[int],
                          workers: int = 50) -> list[int]:
    """macOS/Linux: TCP open check + ADB probe on open ports."""
    def _check(p: int) -> int | None:
        if p in ignored:
            return None
        return p if _tcp_open(ip, p) else None

    open_ports: list[int] = []
    with ThreadPoolExecutor(max_workers=workers) as ex:
        for result in ex.map(_check, ports):
            if result is not None:
                open_ports.append(result)

    found: list[int] = []
    for p in open_ports:
        if adb_probe(ip, p, timeout=1.0):
            found.append(p)
            break
    return found

def _scan_adb_batch(ip: str, ports: list[int], ignored: set[int],
                     workers: int = 50) -> list[int]:
    if sys.platform == "win32":
        return _scan_adb_batch_win(ip, ports, ignored, workers=workers)
    return _scan_adb_batch_unix(ip, ports, ignored, workers=workers)

def adb_connect(ip: str, port: int) -> bool:
    print_info(f"Connecting to {ip}:{port}...")
    try:
        out = adb("connect", f"{ip}:{port}", timeout=10).stdout or ""
    except subprocess.TimeoutExpired:
        return False
    return "connected" in out.lower() and "cannot" not in out.lower() and "failed" not in out.lower()

def find_adb_port(ip: str) -> int:
    # JMGO uses either 5555 or a random port (newer firmware always random)
    known_ports = [5555]
    # Open but known non-ADB ports on JMGO devices
    ignored_ports = [] # Add any known non-ADB ports here if needed

    print_info(f"Scanning known ADB ports on {ip}...")
    for port in known_ports:
        if adb_probe(ip, port):
            print_info(f"ADB found on port {port}")
            if adb_connect(ip, port):
                _on_connected(ip, port)
                return port

    print_warning("ADB not found on known ports. Scanning port range (33000-47000)...")

    # JMGO N3/N5/N5S devices can use random ports in the 33000-47000 range.
    port_order = list(range(33000, 47001))
    total = len(port_order)
    batch_size = 500 if sys.platform == "win32" else 2000
    scanned = 0
    found_port: int | None = None

    for i in range(0, total, batch_size):
        if found_port is not None:
            break
        batch = port_order[i:i + batch_size]
        hits = _scan_adb_batch(ip, batch, ignored_ports, workers=50)
        scanned += len(batch)
        pct = min(scanned * 100 // total, 100)
        sys.stderr.write(f"\r{BLUE}[INFO]{NC} Scanning ports... {pct}%")
        sys.stderr.flush()
        if hits:
            found_port = hits[0]
            sys.stderr.write("\n")
    else:
        sys.stderr.write("\n")

    if found_port is not None:
        print_info(f"ADB found on port {found_port}, connecting...")
        # Restart ADB server to clear stale state from the scan
        adb("kill-server")
        time.sleep(1)
        if adb_connect(ip, found_port):
            _on_connected(ip, found_port)
            return found_port

    print_error(f"Could not find ADB port on {ip}")
    print_info("Make sure ADB over network is enabled on the projector:")
    print("  Settings → About → Build Number (tap 7 times)")
    print("  Developer Options → USB Debugging → ON")
    print("  Developer Options → ADB over network → ON")
    sys.exit(1)

def _on_connected(ip: str, port: int) -> None:
    global ACTIVE_DEVICE_SERIAL
    ACTIVE_DEVICE_SERIAL = f"{ip}:{port}"
    print_status(f"Connected to {ip} on port {port}")
    save_connection(ip, port)
    print_info("Pushing port configuration to device...")
    adb_shell(f"echo {port} > /sdcard/adb_port.txt")
    adb_shell(f"setprop debug.adb.tcp.port {port}")

# ---------------------------------------------------------------------------
# APK directory check
# ---------------------------------------------------------------------------

def check_apk_files() -> None:
    missing = [
        d for d in ("screensaver", "search")
        if not (SCRIPT_DIR / d).is_dir()
    ]
    if missing:
        for d in missing:
            print_warning(f"Directory '{d}' not found")
        print_warning("Some APK directories are missing. Installation may fail.")
        try:
            ans = input("Continue anyway? [yes/No] ").strip().lower()
        except EOFError:
            ans = ""
        if not ans.startswith("y"):
            sys.exit(1)


def pack_apk_files(pack_dir: Path) -> list[Path]:
    if not pack_dir.is_dir():
        return []
    return sorted(
        (
            path
            for path in pack_dir.iterdir()
            if path.is_file() and path.suffix.lower() == ".apk"
        ),
        key=lambda path: path.name.casefold(),
    )


def install_pack_apks(pack_name: str) -> bool:
    pack_dir = SCRIPT_DIR / pack_name
    if not pack_dir.is_dir():
        print_warning(f"{pack_name} directory not found — skipping")
        return False
    apks = pack_apk_files(pack_dir)
    if not apks:
        print_warning(f"No APKs found in {pack_name}")
        return False
    print_info(f"Installing {len(apks)} APK(s) from {pack_name}...")
    for path in apks:
        print(f"Installing {pack_name}/{path.name}...")
        if not adb_install_apk(path):
            print_warning(f"Failed to install {pack_name}/{path.name}")
    return True

# ---------------------------------------------------------------------------
# Tasks
# ---------------------------------------------------------------------------

def task_timezone() -> None:
    print_header()
    if prompt_yes_no("Apply Australia/Sydney timezone?"):
        adb_shell("setprop persist.sys.timezone Australia/Sydney")
        adb_shell("settings put global auto_time_zone 0")
        print_status("Australia/Sydney timezone applied")
        print_info("Automatic time zone disabled to keep the setting")
    else:
        adb_shell("setprop persist.sys.timezone GMT")
        adb_shell("settings put global auto_time_zone 1")
        print_status("Timezone set to GMT")
        print_info("Automatic time zone reenabled")

KATNISS_PACKAGE = "com.google.android.katniss"
VOICE_BRIDGE_PACKAGE = "com.jmgo.tools.voicebridge"
VOICE_BRIDGE_COMPONENT = f"{VOICE_BRIDGE_PACKAGE}/{VOICE_BRIDGE_PACKAGE}.VoiceBridgeService"
VOICE_SERVICES = {
    "voice_recognition_service": f"{KATNISS_PACKAGE}/{KATNISS_PACKAGE}.search.serviceapi.KatnissRecognitionService",
    "voice_interaction_service": f"{KATNISS_PACKAGE}/{KATNISS_PACKAGE}.search.serviceapi.KatnissVoiceInteractionService",
}
VOICE_BACKUP_MARKER = "bonfire_voice_backup_saved"


def _voice_command(command: str) -> str:
    result = adb_shell(command)
    output = ((result.stdout or "") + (result.stderr or "")).strip()
    if result.returncode != 0 or re.search(
        r"(?im)^\s*(?:error\b|exception\b|failure\b|permission denial\b|java\.[\w.]*Exception\b)",
        output,
    ):
        raise RuntimeError(f"{command}: {output or result.returncode}")
    return (result.stdout or "").strip()


def _voice_setting(key: str) -> str:
    return _voice_command(f"settings --user 0 get secure {key}")


def _write_voice_setting(key: str, value: str) -> None:
    if value == "null":
        _voice_command(f"settings --user 0 delete secure {key}")
    else:
        _voice_command(f"settings --user 0 put secure {key} {shlex.quote(value)}")
    if _voice_setting(key) != value:
        raise RuntimeError(f"Could not verify secure setting {key}")


def backup_n5s_voice_services() -> None:
    """Keep the first pre-tuner providers on the device, including absent values."""
    if _voice_setting(VOICE_BACKUP_MARKER) != "1":
        previous = {key: _voice_setting(key) for key in VOICE_SERVICES}
        for key, value in previous.items():
            # Store the literal 'null' sentinel; an absent provider must be deleted on restore.
            backup = f"bonfire_original_{key}"
            _voice_command(f"settings --user 0 put secure {backup} {shlex.quote(value)}")
            if _voice_setting(backup) != value:
                raise RuntimeError(f"Could not save {key}")
        _write_voice_setting(VOICE_BACKUP_MARKER, "1")


def configure_n5s_voice_services() -> None:
    backup_n5s_voice_services()
    previous = {key: _voice_setting(key) for key in VOICE_SERVICES}
    try:
        for key, value in VOICE_SERVICES.items():
            _write_voice_setting(key, value)
    except RuntimeError:
        for key, value in previous.items():
            try:
                _write_voice_setting(key, value)
            except RuntimeError as exc:
                print_warning(f"Provider rollback failed: {exc}")
        raise


def restore_n5s_voice_services() -> None:
    if _voice_setting(VOICE_BACKUP_MARKER) != "1":
        return
    for key, assigned in VOICE_SERVICES.items():
        # Do not overwrite a provider selected by the user after running the tuner.
        if _voice_setting(key) == assigned:
            _write_voice_setting(key, _voice_setting(f"bonfire_original_{key}"))
    _write_voice_setting(VOICE_BACKUP_MARKER, "null")
    for key in VOICE_SERVICES:
        _write_voice_setting(f"bonfire_original_{key}", "null")


def set_n5s_voice_bridge(enabled: bool) -> None:
    if not package_installed(VOICE_BRIDGE_PACKAGE):
        if enabled:
            raise RuntimeError("N5S Voice Bridge is not installed")
        return
    if enabled:
        _voice_command(f"pm enable --user 0 {VOICE_BRIDGE_PACKAGE}")
    broadcast = (
        "am broadcast --user 0 -a action.jmgo.request.accessibility.service "
        f"--es compontentNameStr {VOICE_BRIDGE_COMPONENT} --ez enabled {str(enabled).lower()}"
    )
    commands = [broadcast]
    if not enabled:
        commands.extend([
            f"am force-stop --user 0 {VOICE_BRIDGE_PACKAGE}",
            f"pm disable-user --user 0 {VOICE_BRIDGE_PACKAGE}",
        ])
    errors = []
    for command in commands:
        try:
            _voice_command(command)
        except RuntimeError as exc:
            # Stopping and disabling remain necessary if the OEM receiver fails.
            errors.append(str(exc))
    if errors:
        raise RuntimeError("; ".join(errors))
    for attempt in range(3):
        components = set()
        for component in _voice_setting("enabled_accessibility_services").split(":"):
            package, slash, name = component.partition("/")
            if slash:
                components.add(f"{package}/{package + name if name.startswith('.') else name}")
        if (VOICE_BRIDGE_COMPONENT in components) == enabled:
            return
        if attempt < 2:
            time.sleep(0.3)
    raise RuntimeError("Could not verify N5S Voice Bridge accessibility state")


def install_n5s_voice_bridge(apk: Path) -> None:
    if not adb_install_apk(apk):
        raise RuntimeError("N5S Voice Bridge installation failed")
    _voice_command(f"dumpsys deviceidle whitelist +{VOICE_BRIDGE_PACKAGE}")
    if _voice_command(f"dumpsys deviceidle whitelist ={VOICE_BRIDGE_PACKAGE}").lower() != "true":
        raise RuntimeError("Could not verify N5S Voice Bridge battery exemption")
    _voice_command(f"appops set --user 0 {VOICE_BRIDGE_PACKAGE} RUN_ANY_IN_BACKGROUND allow")
    output = _voice_command(f"appops get --user 0 {VOICE_BRIDGE_PACKAGE} RUN_ANY_IN_BACKGROUND")
    if not _appop_is_allowed(output, "RUN_ANY_IN_BACKGROUND"):
        raise RuntimeError("Could not verify N5S Voice Bridge background permission")
    set_n5s_voice_bridge(True)


def task_google_search() -> None:
    print_header()
    install = prompt_yes_no("Install/configure Google TV Search? Answer No to restore AI Voice")
    variant, details = detect_custom_settings_variant()
    if variant is None:
        print_error(f"Could not determine the voice-search mechanism ({details}). No changes made.")
        return
    print_info(f"Voice-search setup: {CUSTOM_SETTINGS_VARIANTS[variant]['name']} ({details})")
    try:
        if not install:
            if not restore_existing_package("com.jmgo.ai.voice"):
                raise RuntimeError("Could not restore stock AI Voice")
            errors = []
            for restore in (lambda: set_n5s_voice_bridge(False), restore_n5s_voice_services):
                try:
                    restore()
                except RuntimeError as exc:
                    errors.append(str(exc))
            if errors:
                raise RuntimeError("; ".join(errors))
            print_status("AI Voice restored")
            return

        base = SCRIPT_DIR / "search"
        apks = (
            "com.google.android.katniss-2.2.0.FTV.DK.apk",
            "com.google.android.katniss.settings.apk",
            "com.google.android.katniss.settings.speech.apk",
        )
        bridge_apk = base / "BonfireN5SVoiceBridge.apk"
        # Full voice setup is applied to every N5-family variant. Without the
        # Katniss speech providers and the MIC bridge, the physical MIC button
        # opens search but no recognition service handles the audio.
        required = [base / apks[0], bridge_apk]
        missing = [path.name for path in required if not path.is_file()]
        if missing:
            raise RuntimeError(f"Missing search APKs: {', '.join(missing)}")
        # Save providers before installing packages (installs can trigger
        # Android's own provider selection).
        backup_n5s_voice_services()
        for fname in apks:
            path = base / fname
            if not path.is_file():
                print_warning(f"File not found: search/{fname}")
                continue
            if not adb_install_apk(path):
                raise RuntimeError(f"Failed to install {fname}; stock AI Voice was not disabled")
        if not package_installed(KATNISS_PACKAGE):
            raise RuntimeError("Google TV Search not found after install")
        _voice_command(f"pm grant --user 0 {KATNISS_PACKAGE} android.permission.RECORD_AUDIO")
        _voice_command(f"appops set --user 0 {KATNISS_PACKAGE} SYSTEM_ALERT_WINDOW allow")
        permissions = _voice_command(f"dumpsys package {KATNISS_PACKAGE}")
        if not _permission_is_granted(permissions, "android.permission.RECORD_AUDIO", 0):
            raise RuntimeError("Could not verify Google microphone permission")
        overlay = _voice_command(f"appops get --user 0 {KATNISS_PACKAGE} SYSTEM_ALERT_WINDOW")
        if not _appop_is_allowed(overlay, "SYSTEM_ALERT_WINDOW"):
            raise RuntimeError("Could not verify Google overlay permission")
        configure_n5s_voice_services()
        try:
            install_n5s_voice_bridge(bridge_apk)
        except RuntimeError:
            try:
                set_n5s_voice_bridge(False)
            except RuntimeError as exc:
                print_warning(f"Could not disable Voice Bridge after setup failure: {exc}")
            raise
        if package_installed("com.jmgo.ai.voice"):
            _voice_command("pm uninstall --user 0 com.jmgo.ai.voice")
        if package_installed("com.jmgo.ai.voice"):
            raise RuntimeError("Stock AI Voice is still installed for user 0")
        print_info("In SmartTube select external microphone for voice search.")
        print_info("In an app: select its microphone icon, then hold MIC, speak and release.")
        print_status("Google TV Search installed with voice bridge")
        print_warning("Verify speech with the physical remote; software checks cannot confirm microphone audio.")
    except RuntimeError as exc:
        print_error(f"Voice-search setup was not completed: {exc}")

def _prompt_screensaver_timeout() -> int:
    """Let the user pick screen-off timeout. Returns value in milliseconds."""
    timeouts = [
        ("1 minute",   60000),
        ("2 minutes",  120000),
        ("5 minutes",  300000),
        ("10 minutes", 600000),
        ("30 minutes", 1800000),
    ]
    default_idx = 2  # 5 minutes — verified working default
    print()
    print(f"  {BOLD}Screen-off timeout (before screensaver starts):{NC}\n")
    for i, (label, _) in enumerate(timeouts, 1):
        marker = f" {GREEN}(default){NC}" if i - 1 == default_idx else ""
        print(f"  {CYAN}{i}{NC}) {label}{marker}")
    print()
    try:
        resp = input(f"  {BLUE}[INPUT]{NC} Choose timeout [1-{len(timeouts)}]: ").strip()
    except EOFError:
        resp = ""
    if not resp:
        return timeouts[default_idx][1]
    try:
        choice = int(resp)
        if 1 <= choice <= len(timeouts):
            return timeouts[choice - 1][1]
    except ValueError:
        pass
    print_info(f"Invalid choice, using default ({timeouts[default_idx][0]})")
    return timeouts[default_idx][1]


def task_screensaver() -> None:
    dreamx_pkg = "com.google.android.apps.tv.dreamx"
    dreamx_component = (
        f"{dreamx_pkg}/com.google.android.apps.tv.dreamx.service.Backdrop"
    )
    stock_component = "com.jmgo.os.dream/com.jmgo.os.dream.core.service.JGDreamService"
    print_header()
    print(f"  {BOLD}Screensaver options:{NC}\n")
    print(f"  {CYAN}1{NC}) Install Google TV Screensaver")
    print(f"  {CYAN}2{NC}) Disable screensaver completely")
    print(f"  {CYAN}3{NC}) Restore stock JMGO screensaver")
    print()
    try:
        resp = input(f"  {BLUE}[INPUT]{NC} Choose option [1-3] (Enter to skip): ").strip()
    except EOFError:
        resp = ""
    if resp == "1":
        apk = SCRIPT_DIR / "screensaver" / "AmbientMode.apk"
        if not apk.is_file():
            print_error("AmbientMode.apk not found in screensaver/")
            return
        timeout_ms = _prompt_screensaver_timeout()
        print_info("Installing Google TV Screensaver...")
        if not adb_install_apk(apk):
            print_error("Screensaver installation failed — stock screensaver was NOT replaced.")
            return
        if not package_installed(dreamx_pkg):
            print_error(f"{dreamx_pkg} not found after install — stock screensaver was NOT replaced.")
            return
        adb_shell(f"settings put secure screensaver_components {dreamx_component}")
        adb_shell(f"settings put secure screensaver_default_component {dreamx_component}")
        adb_shell(f"settings put system screen_off_timeout {timeout_ms}")
        adb_shell("settings put secure lockscreen.disabled 1")
        adb_shell("settings put secure screensaver_enabled 1")
        adb_shell("settings put secure screensaver_activate_on_dock 1")
        adb_shell("settings put secure screensaver_activate_on_sleep 1")
        adb_shell("settings put global stay_on_while_plugged_in 0")
        print_status(f"Google TV Screensaver configured (timeout: {timeout_ms // 60000} min)")
    elif resp == "2":
        print_info("Disabling screensaver completely...")
        adb_shell("settings put secure screensaver_enabled 0")
        adb_shell("settings put secure screensaver_activate_on_dock 0")
        adb_shell("settings put secure screensaver_activate_on_sleep 0")
        adb_shell(f"settings put secure screensaver_components {stock_component}")
        adb_shell(f"settings put secure screensaver_default_component {stock_component}")
        adb_shell("settings put system screen_off_timeout 2147483647")
        adb_shell("settings put secure lockscreen.disabled 0")
        adb_shell("settings put global stay_on_while_plugged_in 0")
        if package_installed(dreamx_pkg):
            print_info("Removing Google TV Screensaver...")
            adb_shell(f"pm uninstall --user 0 {dreamx_pkg}")
            if package_installed(dreamx_pkg):
                print_warning("Could not remove Google TV Screensaver — it may still be installed.")
        print_status("Screensaver disabled — screen will stay on indefinitely")
    elif resp == "3":
        if package_installed("com.jmgo.os.dream"):
            print_info("Restoring stock JMGO screensaver...")
            adb_shell(f"settings put secure screensaver_components {stock_component}")
            adb_shell(f"settings put secure screensaver_default_component {stock_component}")
            adb_shell("settings put secure screensaver_enabled 1")
            adb_shell("settings put secure screensaver_activate_on_dock 1")
            adb_shell("settings put secure screensaver_activate_on_sleep 1")
            adb_shell("settings put system screen_off_timeout 60000")
            adb_shell("settings put secure lockscreen.disabled 0")
            adb_shell("settings put global stay_on_while_plugged_in 0")
            if package_installed(dreamx_pkg):
                print_info("Removing Google TV Screensaver...")
                adb_shell(f"pm uninstall --user 0 {dreamx_pkg}")
                if package_installed(dreamx_pkg):
                    print_warning("Could not remove Google TV Screensaver — it may still be installed.")
            print_status("Stock JMGO screensaver restored")
        else:
            print_error("Stock screensaver package (com.jmgo.os.dream) not found on device")
    else:
        print_info("No changes made")


CUSTOM_SETTINGS_APK = "JmGOSetting-clone.apk"


CUSTOM_SETTINGS_VARIANTS = {
    "n3": {
        "name": "JMGO N3",
        "apk": CUSTOM_SETTINGS_APK,
        "stock_versions": {"8.1.821"},
        "model_codes": {"K970"},
    },
    "n5": {
        "name": "JMGO N5",
        "apk": CUSTOM_SETTINGS_APK,
        "stock_versions": {"8.1.959"},
        "model_codes": {"K931CN"},
    },
    "n5s": {
        "name": "JMGO N5S",
        "apk": CUSTOM_SETTINGS_APK,
        "stock_versions": {"8.1.987", "8.1.991"},
        "model_codes": {"KD11CN"},
    },
}


def _stock_settings_version() -> str:
    output = adb_shell("dumpsys package com.jmgo.setting.x").stdout or ""
    match = re.search(r"(?m)^\s*versionName=([^\s]+)\s*$", output)
    return match.group(1) if match else ""


def detect_custom_settings_variant() -> tuple[str | None, str]:
    """Identify the family for model-specific voice setup and app cleanup."""
    stock_version = _stock_settings_version()
    model_values = {
        value.upper()
        for value in (
            _getprop("ro.product.model"),
            _getprop("ro.product.device"),
            _getprop("ro.product.device.jmgo"),
        )
        if value
    }

    evidence: set[str] = set()
    for key, variant in CUSTOM_SETTINGS_VARIANTS.items():
        if stock_version in variant["stock_versions"]:
            evidence.add(key)
        if model_values.intersection(variant["model_codes"]):
            evidence.add(key)

    for model in model_values:
        if model == "K970":
            evidence.add("n3")
        elif "N5S" in model:
            evidence.add("n5s")
        elif "N5" in model:
            evidence.add("n5")

    details = (
        f"stock settings {stock_version or 'unknown'}, "
        f"model {', '.join(sorted(model_values)) or 'unknown'}"
    )
    if len(evidence) != 1:
        return None, details
    return evidence.pop(), details


def task_custom_settings() -> None:
    settings_pkg = "com.jmgo.setting.clone"
    print_header()
    if not prompt_yes_no("Install or update Custom Settings (JMGO Clone)?"):
        print_info("No changes made")
        return

    if not package_installed("com.jmgo.setting.x"):
        print_error(
            "Stock JMGO Settings (com.jmgo.setting.x) was not found on the "
            "connected device. No APK was installed."
        )
        return

    apk = SCRIPT_DIR / "settings" / CUSTOM_SETTINGS_APK
    if not apk.is_file():
        print_error(f"{CUSTOM_SETTINGS_APK} not found in settings/")
        return

    print_info(f"Using the universal {CUSTOM_SETTINGS_APK}.")
    print_info("Installing JMGO Settings Clone alongside the stock settings app...")
    adb_shell(f"am force-stop {settings_pkg}")
    if not adb_install_apk(apk, timeout=300, allow_downgrade=True):
        print_error("JMGO Settings Clone installation failed — stock settings were not changed.")
        return

    if not package_installed(settings_pkg):
        print_error(
            f"{settings_pkg} is not listed after install — stock settings were not changed."
        )
        return

    required_permissions = (
        "android.permission.WRITE_SECURE_SETTINGS",
        "android.permission.CHANGE_CONFIGURATION",
    )
    for permission in required_permissions:
        adb_shell(f"pm grant {settings_pkg} {permission}")
    permission_state = adb_shell(f"dumpsys package {settings_pkg}").stdout or ""
    missing_permissions = [
        permission
        for permission in required_permissions
        if f"{permission}: granted=true" not in permission_state
    ]
    if missing_permissions:
        print_warning(
            "Custom Settings was installed, but required permissions could not be "
            f"verified ({', '.join(missing_permissions)}); some General settings "
            "may not be applied."
        )

    adb_shell(f"appops set {settings_pkg} SYSTEM_ALERT_WINDOW allow")

    # Enable the clone's Settings-button interception service so the physical
    # SETTINGS key is captured by the clone instead of the stock app. The
    # short/long-press MODE (original/simple/full menu) lives in the app's
    # private SharedPreferences and cannot be changed via ADB without root;
    # the user selects that once in: General > Remote keys > Settings.
    settings_button_service = (
        f"{settings_pkg}/com.jmgo.setting.recovery.SettingsButtonAccessibilityService"
    )
    adb_shell(
        "am broadcast --user 0 -a action.jmgo.request.accessibility.service "
        f"--es compontentNameStr {settings_button_service} --ez enabled true"
    )
    print_status("JMGO Settings Clone installed; stock settings remain available")
    print_info(
        "Settings button interception enabled. To make the SETTINGS key open the "
        "clone, go to General > Remote keys > Settings and bind Short press to "
        "Full menu (one-time, stored in app preferences)."
    )

def task_disable_chinese() -> None:
    # Apps that must not be removed until their replacement from earlier menu steps
    # is confirmed installed on the device.
    replacement_apps: dict[str, tuple[str, str]] = {
        "com.jmgo.ai.voice": ("com.google.android.katniss", "Google TV Search (menu item 2)"),
        "com.jmgo.os.dream": ("com.google.android.apps.tv.dreamx", "Google TV Screensaver (menu item 3)"),
    }
    # com.bajintech.assistant is deliberately protected: reports from N5-series
    # devices link its removal to loss of USB host functionality.
    removable_pkgs = [
        "com.jmgo.ai.voice",
        "com.jmgo.helpcenter",
        "com.jmgo.miiot",
        "com.jmgo.os.dream",
        "com.jmgo.os.guide",
    ]
    # Screen mirroring (the only cast receiver on this firmware) must stay
    # available. Older script versions hid it via `pm uninstall --user 0`, so
    # self-heal it here regardless of the Yes/No choice.
    cast_pkg = "com.jmgo.holacast.x"
    print_header()
    if package_installed(cast_pkg):
        print_info(f"Screen mirroring ({cast_pkg}) is kept enabled.")
    elif restore_existing_package(cast_pkg):
        print_status(f"Screen mirroring restored: {cast_pkg}")
    if prompt_yes_no("Disable selected Chinese stock apps? Answer No to restore them"):
        print_info("Disabling Chinese apps...")
        # Cache installed packages once to avoid repeated ADB calls.
        installed_pkgs = adb_shell("pm list packages").stdout or ""
        installed_lines = installed_pkgs.splitlines()
        skipped = 0
        disabled = 0
        for pkg in removable_pkgs:
            if pkg == "com.jmgo.ai.voice":
                variant, _ = detect_custom_settings_variant()
                if variant not in ("n3", "n5"):
                    print_info("Keeping AI Voice: N5S native MIC handling or unknown model.")
                    skipped += 1
                    continue
            if pkg in replacement_apps:
                repl_pkg, repl_name = replacement_apps[pkg]
                if f"package:{repl_pkg}" not in installed_lines:
                    print_warning(
                        f"Skipping {pkg}: install {repl_name} first."
                    )
                    skipped += 1
                    continue
            adb_shell(f"pm uninstall --user 0 {pkg}")
            disabled += 1
        if disabled == 0:
            print_warning("No apps were disabled — install their replacements first, then re-run.")
        elif skipped:
            print_warning(f"Skipped {skipped} app(s); see the reasons above.")
            print_status("Some Chinese apps disabled")
        else:
            print_status("Chinese apps disabled")
    else:
        print_info("Reenabling stock apps...")
        restored = sum(restore_existing_package(pkg) for pkg in removable_pkgs)
        if restored == len(removable_pkgs):
            print_status("Stock apps reenabled and verified")
        else:
            print_warning(
                f"Restored {restored}/{len(removable_pkgs)} stock apps; see warnings above."
            )

def task_ru_addons() -> None:
    print_header()
    if not prompt_yes_no("Install RU Addons?"):
        print_info("OK, skipping RU addons")
        return
    if install_pack_apks("rupack"):
        print_status("RU addons installation completed")


def task_user_apps() -> None:
    print_header()
    if install_pack_apks("userpack"):
        print_status("User apps installation completed")

def task_fix_permissions() -> None:
    print_header()
    if not prompt_yes_no("Fix User Apps Permissions?"):
        print_info("OK, skipping permissions fix")
        return
    print_info("Fixing user apps permissions...")
    user = adb_shell("am get-current-user")
    user_id = (user.stdout or "").strip()
    if user.returncode != 0 or not user_id.isdecimal():
        print_error("Could not determine the current Android user; permissions were not changed")
        return
    result = adb_shell(f"pm list packages -3 --user {user_id}")
    lines = (result.stdout or "").splitlines()
    if result.returncode != 0 or (result.stderr or "").strip() or any(
        not re.fullmatch(r"package:[\w.]+", line.strip()) for line in lines if line.strip()
    ):
        print_error("Could not list user apps; permissions were not changed")
        return
    packages = [line.strip().split(":", 1)[1] for line in lines if line.strip()]
    if not packages:
        print_info("No user apps found")
        return
    total = len(packages)
    perms = [
        "android.permission.ACCESS_COARSE_LOCATION",
        "android.permission.READ_LOGS",
        "android.permission.RECORD_AUDIO",
        "android.permission.WRITE_SECURE_SETTINGS",
    ]
    appops = [
        "RUN_ANY_IN_BACKGROUND",
        "SYSTEM_ALERT_WINDOW",
        "QUERY_ALL_PACKAGES",
        "REQUEST_INSTALL_PACKAGES",
        "RUN_IN_BACKGROUND",
    ]
    appop_permissions = {
        op: f"android.permission.{op}"
        for op in ("SYSTEM_ALERT_WINDOW", "QUERY_ALL_PACKAGES", "REQUEST_INSTALL_PACKAGES")
    }
    failed = []

    def apply(command: str) -> None:
        result = adb_shell(command)
        output = " ".join(((result.stdout or "") + "\n" + (result.stderr or "")).split())
        if result.returncode != 0 or output:
            print_warning(f"{command}: exit {result.returncode}: {output or 'no output'}; "
                          "permission state is checked separately")

    for i, pkg in enumerate(packages, 1):
        print(f"{YELLOW}[{i}/{total}] Processing:{NC} {pkg}")
        result = adb_shell(f"dumpsys package {pkg}")
        requested = _requested_permissions(result.stdout or "", pkg)
        if result.returncode != 0 or (result.stderr or "").strip() or requested is None:
            failed.append(pkg)
            print_warning(f"{pkg}: Could not read declared permissions; app skipped")
            continue
        package_perms = [perm for perm in perms if perm in requested]
        package_appops = [op for op in appops if op not in appop_permissions
                          or appop_permissions[op] in requested]
        skipped = len(perms) + len(appops) - len(package_perms) - len(package_appops)
        if skipped:
            print_info(f"{pkg}: Skipped {skipped} permission checks not declared by this app")
        for perm in package_perms:
            apply(f"pm grant --user {user_id} {pkg} {perm}")
        for op in package_appops:
            apply(f"appops set --user {user_id} {pkg} {op} allow")
        # This command normally prints an acknowledgement on success.
        result = adb_shell(f"dumpsys deviceidle whitelist +{pkg}")
        if result.returncode != 0:
            print_warning(f"{pkg}: deviceidle whitelist write failed (exit {result.returncode})")

        unconfirmed = []
        if package_perms:
            result = adb_shell(f"dumpsys package {pkg}")
        for perm in package_perms:
            if result.returncode != 0 or (result.stderr or "").strip() or not _permission_is_granted(
                result.stdout or "", perm, int(user_id)
            ):
                unconfirmed.append(perm)
        for op in package_appops:
            result = adb_shell(f"appops get --user {user_id} {pkg} {op}")
            result = _repair_appop_uid_override(pkg, op, result, user_id=user_id)
            output = (result.stdout or "") + "\n" + (result.stderr or "")
            if result.returncode != 0 or not _appop_is_allowed(output, op):
                unconfirmed.append(op)
                print_warning(f"{pkg}: {op} readback (exit {result.returncode}): "
                              f"{' '.join(output.split()) or 'no output'}")
        result = adb_shell(f"dumpsys deviceidle whitelist ={pkg}")
        if result.returncode != 0 or (result.stdout or "").strip().lower() != "true":
            unconfirmed.append("deviceidle whitelist")
        if unconfirmed:
            failed.append(pkg)
            print_warning(f"{pkg}: Could not verify: {', '.join(unconfirmed)}")
        else:
            print_status(f"{pkg}: Requested permissions and deviceidle whitelist verified")
    if failed:
        print_warning(f"Permissions verified for {total - len(failed)}/{total} user apps; "
                      f"unconfirmed apps: {', '.join(failed)}")
    else:
        print_status(f"Permissions verified for all {total} user apps")


def _requested_permissions(output: str, package: str) -> set[str] | None:
    """Read declarations from the active package, excluding old system copies.

    Android omits the requested section for apps with no permissions. None means
    that the package dump could not be identified, not an empty declaration set.
    """
    in_packages = False
    package_indent = None
    requested_indent = None
    permissions: set[str] = set()
    for line in output.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        indent = len(line) - len(line.lstrip())
        if package_indent is not None and indent <= package_indent:
            return permissions
        if indent == 0:
            in_packages = stripped == "Packages:"
        if in_packages and re.fullmatch(
            rf"Package \[{re.escape(package)}\](?: \([^\n]*\))?:", stripped
        ):
            package_indent = indent
            continue
        if package_indent is None:
            continue
        if requested_indent is not None:
            if indent > requested_indent:
                if not re.fullmatch(r"[\w.]+", stripped):
                    return None
                permissions.add(stripped)
                continue
            requested_indent = None
        if stripped == "requested permissions:":
            requested_indent = indent
    return permissions if package_indent is not None else None


def _permission_is_granted(output: str, permission: str, user_id: int) -> bool:
    """Read install permissions and only the selected user's runtime permissions."""
    current_user = None
    section = None
    section_indent = -1
    install_granted = False
    runtime_granted = None
    for line in output.splitlines():
        stripped = line.strip()
        indent = len(line) - len(line.lstrip())
        if stripped and indent <= section_indent:
            section = None
        user = re.match(r"User (\d+):", stripped)
        if user:
            current_user = int(user.group(1))
        if stripped in ("install permissions:", "runtime permissions:"):
            section = stripped
            section_indent = indent
            continue
        match = re.fullmatch(rf"{re.escape(permission)}: granted=(true|false)(?:,.*)?", stripped)
        if match:
            if section == "install permissions:":
                install_granted = match.group(1) == "true"
            elif section == "runtime permissions:" and current_user == user_id:
                runtime_granted = match.group(1) == "true"
    return install_granted if runtime_granted is None else runtime_granted

def _appop_is_allowed(output: str, operation: str) -> bool:
    """Read this AppOp's mode, giving a UID override priority over package mode."""
    mode_pattern = rf"{re.escape(operation)}[ \t]*:[ \t]*(\w+)\b"
    # Android prints the UID override on the same line as the operation.
    # It takes precedence even when the package itself has an allow entry.
    for prefix in (r"Uid[ \t]+mode:[ \t]*", ""):
        match = re.search(
            rf"^[ \t]*{prefix}{mode_pattern}", output, re.MULTILINE | re.IGNORECASE
        )
        if match:
            return match.group(1).lower() == "allow"
    # An operation at its platform default can have no stored entry at all.
    return re.fullmatch(r"\s*No operations\.\s*Default mode:[ \t]*allow\s*",
                        output, re.IGNORECASE) is not None


def _repair_appop_uid_override(
    package: str, operation: str, result: subprocess.CompletedProcess,
    *, user_id: str | None = None,
) -> subprocess.CompletedProcess:
    """Repair an observed UID restriction after setting the package mode to allow.

    Only touch this operation when a successful read explicitly shows a UID
    override. A successful write is not proof: always return a fresh readback.
    """
    if result.returncode != 0 or (result.stderr or "").strip():
        return result
    match = re.search(
        rf"^[ \t]*Uid[ \t]+mode:[ \t]*{re.escape(operation)}[ \t]*:[ \t]*"
        r"(ignore|deny|foreground|default)\b",
        result.stdout or "", re.MULTILINE | re.IGNORECASE,
    )
    if not match:
        return result
    user_option = f" --user {user_id}" if user_id is not None else ""
    print_info(f"{package}: {operation} has UID mode {match.group(1)}; allowing and rechecking")
    write = adb_shell(f"appops set{user_option} --uid {package} {operation} allow")
    output = " ".join(((write.stdout or "") + "\n" + (write.stderr or "")).split())
    if write.returncode != 0 or output:
        print_warning(f"{package}: UID AppOp {operation}: appops set exit {write.returncode}: "
                      f"{output or 'no output'}; permission state is checked separately")
    return adb_shell(f"appops get{user_option} {package} {operation}")


def task_fix_store_permissions() -> None:
    print_header()
    print_info("Fixing app store install permissions...\n")
    app_stores = [
        ("ru.vk.store", "RuStore"),
        ("ru.vk.store.tv", "RuStore TV"),
        ("com.aptoide.partners", "Aptoide"),
        ("com.aptoide.tv", "Aptoide TV"),
        ("cm.aptoidetv.pt", "Aptoide TV"),
        ("com.aurora.store", "Aurora Store"),
        ("com.aurora.store.nightly", "Aurora Store Nightly"),
        ("org.fdroid.fdroid", "F-Droid"),
        ("com.looker.droidify", "Droid-ify"),
        ("com.apkpure.aegon", "APKPure"),
        ("dev.nicehash", "Emotn Store"),
        ("com.nicehash.tvstore", "Emotn Store TV"),
        ("com.overseas.store.appstore", "Overseas Store"),
    ]
    all_pkgs = (adb_shell("pm list packages -3").stdout or "").replace("\r", "")
    installed = {ln.split(":", 1)[1].strip() for ln in all_pkgs.splitlines() if ":" in ln}

    found: list[tuple[str, str]] = []
    for pkg, name in app_stores:
        if pkg in installed:
            check = (adb_shell(f"appops get {pkg} REQUEST_INSTALL_PACKAGES").stdout or "")
            if "no uid" in check.lower():
                print_warning(f"{name} ({pkg}) — removed for current user, skipping")
            else:
                found.append((pkg, name))

    if not found:
        print_warning("No known app stores found, searching by keywords...")
        for pkg in installed:
            low = pkg.lower()
            if ("store" in low or "market" in low or "install" in low) and not pkg.startswith(("com.android.vending", "com.google.android")):
                found.append((pkg, pkg))

    if not found:
        print_warning("No app stores found on device")
        return

    print(f"  Found {GREEN}{len(found)}{NC} app store(s)\n")
    result = adb_shell("settings put secure install_non_market_apps 1")
    if result.returncode == 0:
        print_status("install_non_market_apps = 1\n")
    else:
        output = " ".join(((result.stdout or "") + "\n" + (result.stderr or "")).split())
        print_warning(
            f"Auxiliary setting install_non_market_apps failed (exit {result.returncode}): "
            f"{output or 'no output'}; install permission is checked separately"
        )

    required_op = "REQUEST_INSTALL_PACKAGES"
    optional_ops = ("RUN_IN_BACKGROUND", "RUN_ANY_IN_BACKGROUND",
                    "SYSTEM_ALERT_WINDOW", "QUERY_ALL_PACKAGES")
    failed: list[str] = []
    for pkg, name in found:
        print(f"  {BOLD}{CYAN}{name}{NC} {DIM}({pkg}){NC}")
        result = adb_shell(f"dumpsys package {pkg}")
        requested = _requested_permissions(result.stdout or "", pkg)
        if result.returncode != 0 or (result.stderr or "").strip() or requested is None:
            print_warning(f"{name} ({pkg}): Could not read declared permissions; app skipped")
            failed.append(f"{name} ({pkg})")
            continue
        if f"android.permission.{required_op}" not in requested:
            print_warning(f"{name} ({pkg}): REQUEST_INSTALL_PACKAGES is not declared; app skipped")
            failed.append(f"{name} ({pkg})")
            continue
        package_ops = (required_op, *(op for op in optional_ops
            if op in ("RUN_IN_BACKGROUND", "RUN_ANY_IN_BACKGROUND")
            or f"android.permission.{op}" in requested))
        skipped = 1 + len(optional_ops) - len(package_ops)
        if skipped:
            print_info(f"{name}: Skipped {skipped} optional permission checks not declared by this app")
        for op in package_ops:
            result = adb_shell(f"appops set {pkg} {op} allow")
            output = " ".join(((result.stdout or "") + "\n" + (result.stderr or "")).split())
            # Some Android versions report AppOps errors even with exit code 0.
            if result.returncode != 0 or output:
                label = "Required AppOp" if op == required_op else "Optional AppOp"
                print_warning(
                    f"{label} {op}: appops set exit {result.returncode}: {output or 'no output'}; "
                    "this does not determine install permission, which is verified below"
                )
        adb_shell(f"dumpsys deviceidle whitelist +{pkg}")

        result = adb_shell(f"appops get {pkg} {required_op}")
        result = _repair_appop_uid_override(pkg, required_op, result)
        output = (result.stdout or "") + "\n" + (result.stderr or "")
        if result.returncode == 0 and _appop_is_allowed(output, required_op):
            print_status(f"{name} ({pkg}): Install from unknown sources allowed")
        else:
            details = " ".join(output.split()) or "no output"
            print_error(
                f"{name} ({pkg}): Install from unknown sources FAILED "
                f"(appops get exit {result.returncode}: {details})"
            )
            failed.append(f"{name} ({pkg})")
    print()
    if not failed:
        print_status("Store install permission verified for all found app stores")
    else:
        print_warning("Install permission could not be verified for some app stores: " + ", ".join(failed))


def task_disable_updates() -> None:
    print_header()
    update_pkgs = [
        "com.jmgo.update",
        "com.jmgo.remotecontrolota",
    ]
    if prompt_yes_no("Disable JMGO OTA updates?"):
        print_info("Disabling JMGO update services...")
        for pkg in update_pkgs:
            adb_shell(f"pm uninstall -k --user 0 {pkg}")
        print_status("JMGO OTA updates disabled")
    else:
        print_info("Reenabling JMGO update services...")
        for pkg in update_pkgs:
            adb_shell(f"cmd package install-existing {pkg}")
        print_status("JMGO OTA updates reenabled")


def _getprop(name: str) -> str:
    return (adb_shell(f"getprop {name}").stdout or "").strip()


def _set_csv_token(value: str, token: str, enabled: bool) -> str:
    tokens = [item.strip() for item in value.split(",") if item.strip()]
    tokens = [item for item in tokens if item != token]
    if enabled:
        tokens.append(token)
    return ",".join(tokens)


def _restart_original_settings() -> None:
    adb_shell("am force-stop com.jmgo.setting.x")


def task_enable_3d() -> None:
    print_header()
    print_warning(
        "3D activation for the original settings is temporary and is lost after a projector reboot.\n"
        "The custom settings clone exposes its 3D menu without this task.\n"
    )

    video_option = _getprop("jmgo.option.video")
    if not video_option:
        print_error("jmgo.option.video is empty; refusing to replace an unknown device configuration.")
        return

    if prompt_yes_no("Enable 3D menu in the original settings?"):
        updated_video_option = _set_csv_token(video_option, "thrD", True)
        three_dimension_modes = _getprop("jmgo.mode.threeDimension")
        if not three_dimension_modes:
            three_dimension_modes = "autoOnlyHdmi,lr,tb"

        adb_shell("setprop jmgo.enable3d true")
        adb_shell(f"setprop jmgo.option.video {updated_video_option}")
        adb_shell(f"setprop jmgo.mode.threeDimension {three_dimension_modes}")
        _restart_original_settings()

        enabled = _getprop("jmgo.enable3d") == "true"
        option_enabled = "thrD" in _getprop("jmgo.option.video").split(",")
        if not enabled or not option_enabled:
            print_error("3D properties were not accepted by the projector.")
            return

        print_status("3D menu enabled in the original settings")
        print_info("Reopen the original Settings, then open Picture -> Advanced -> 3D Mode.")
    else:
        updated_video_option = _set_csv_token(video_option, "thrD", False)
        adb_shell("setprop jmgo.enable3d false")
        adb_shell(f"setprop jmgo.option.video {updated_video_option}")
        _restart_original_settings()

        option_enabled = "thrD" in _getprop("jmgo.option.video").split(",")
        if option_enabled:
            print_error("Could not remove the temporary 3D menu option.")
            return

        print_status("Temporary 3D menu disabled in the original settings")


def task_reboot() -> None:
    print_header()
    if prompt_yes_no("Reboot Bonfire OS?"):
        print_info("Rebooting device...")
        adb_shell("setprop ctl.restart zygote")
        print_status("Reboot command sent")
    else:
        print_info("OK, no reboot")

# ---------------------------------------------------------------------------
# Menu
# ---------------------------------------------------------------------------

MENU = [
    ("Apply Australia/Sydney timezone",        task_timezone),
    ("Install Google TV Search",               task_google_search),
    ("Configure Screensaver",                  task_screensaver),
    ("Install Custom Settings (JMGO Clone)",   task_custom_settings),
    ("Disable or Restore Chinese Stock Apps",  task_disable_chinese),
    ("Install RU Addons",                      task_ru_addons),
    ("Install User Apps (userpack)",           task_user_apps),
    ("Fix User Apps Permissions",              task_fix_permissions),
    ("Fix App Store Permissions",              task_fix_store_permissions),
    ("Disable JMGO OTA Updates",               task_disable_updates),
    ("Enable 3D Settings",                     task_enable_3d),
    ("Reboot Bonfire OS",                      task_reboot),
]

def show_menu() -> None:
    print_header()
    print(f"  {BOLD}Select an action:{NC}\n")
    for i, (name, _) in enumerate(MENU, 1):
        print(f"  {CYAN}{i:>2}{NC}) {name}")
    print()
    print(f"  {GREEN} A{NC}) Run ALL (1-{len(MENU)} sequentially)")
    print(f"  {RED} Q{NC}) Quit\n")

def run_task(idx: int) -> None:
    name, fn = MENU[idx]
    print(f"\n{BOLD}━━━ {CYAN}[{idx+1}] {name}{NC} {BOLD}━━━{NC}\n")
    fn()
    print()
    print_status(f"Done: {name}\n")
    press_enter()

def run_all() -> None:
    total = len(MENU)
    for i, (name, fn) in enumerate(MENU, 1):
        print(f"\n{BOLD}━━━ {CYAN}[{i}/{total}] {name}{NC} {BOLD}━━━{NC}\n")
        fn()
        print()
    print_header()
    print(f"{GREEN}{BOLD}[*] All done! Have fun!{NC}\n")
    print("========================================")
    press_enter()

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

IP_RE   = re.compile(r"^\d{1,3}(\.\d{1,3}){3}$")
IP_PORT = re.compile(r"^\d{1,3}(\.\d{1,3}){3}:\d+$")

def connect_from_args() -> None:
    if len(sys.argv) >= 2:
        arg = sys.argv[1]
        if IP_PORT.match(arg):
            ip, port = arg.split(":")
            if adb_connect(ip, int(port)):
                _on_connected(ip, int(port))
            else:
                print_error(f"Failed to connect to {arg}")
            return
        if IP_RE.match(arg):
            find_adb_port(arg)
            return
        print_error(f"Invalid argument: {arg}")
        print(f"\n  Usage: {sys.argv[0]} [ip:port]")
        print("  Examples:")
        print(f"    {sys.argv[0]} 192.168.3.11:37705   — connect directly")
        print(f"    {sys.argv[0]} 192.168.3.11         — auto-detect port")
        print(f"    {sys.argv[0]}                      — interactive mode")
        sys.exit(1)

    # Interactive
    default_ip, default_port = load_connection()
    ip_prompt = "Type IP of device"
    ip_prompt += f" [default: {default_ip}]" if default_ip else " [ex. 192.168.3.11]"
    ip_prompt += ": "
    try:
        ip = input(f"{BLUE}[INPUT]{NC} {ip_prompt}").strip() or default_ip
    except EOFError:
        ip = default_ip
    if not IP_RE.match(ip):
        print_error("Invalid IP format")
        sys.exit(1)

    port_prompt = "Port (leave empty for auto-detect"
    if default_port:
        port_prompt += f", default: {default_port}, type 'a' to force auto-detect"
    port_prompt += "): "
    try:
        port = input(f"{BLUE}[INPUT]{NC} {port_prompt}").strip()
    except EOFError:
        port = ""
    if port.lower() == "a":
        port = ""
    elif not port:
        port = default_port

    clear_screen()
    print_header()

    if port:
        if adb_connect(ip, int(port)):
            _on_connected(ip, int(port))
        else:
            print_error(f"Failed to connect to {ip}:{port}")
    else:
        find_adb_port(ip)

def main() -> None:
    global ACTIVE_DEVICE_SERIAL
    check_adb()
    ACTIVE_DEVICE_SERIAL = None
    adb("disconnect")
    adb("kill-server")
    print_header()
    connect_from_args()
    wait_for_device()
    check_connection()
    check_apk_files()

    while True:
        show_menu()
        try:
            choice = input(f"  {BLUE}[INPUT]{NC} Choice: ").strip()
        except EOFError:
            print()
            return
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(MENU):
                run_task(idx)
            else:
                print_error("Invalid choice")
                time.sleep(1)
        elif choice.lower() == "a":
            run_all()
        elif choice.lower() == "q":
            print()
            print_info("Bye!")
            print()
            return
        else:
            print_error(f"Invalid choice. Enter 1-{len(MENU)}, A, or Q.")
            time.sleep(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
        print_info("Interrupted")
        sys.exit(130)
