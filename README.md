# 坚果投影仪工具箱（JMGO Bonfire OS Tuner）

针对 **JMGO N5 / N5 Ultra / N5S**（机型 `K941CN` / `K931CN`，Android 14，Bonfire OS）的 ADB 定制工具箱。原项目来自第三方 N5/N5S 工具包，本仓库是面向 N5 Ultra 实际设备的定制版本。

> 版本：`2026.09.12-au-sydney`

## 功能

- 时区改为 **Australia/Sydney**，并关闭自动时区
- 安装 **Google TV 搜索**：Katniss 三件套 + 语音识别服务 + 语音键桥接
  - 输入框内按遥控器语音键 → 搜狗语音打字
  - 平时按语音键 → 谷歌语音搜索
- 配置 **Google TV 屏保**（Google Backdrop），默认 5 分钟熄屏
- 安装 **JMGO 设置克隆版**，可通过物理设置键拦截打开
- 禁用/恢复中文预装应用，**保护投屏**（`com.jmgo.holacast.x` 不被禁用，且有自愈）
- 安装 RU 插件（SmartTube / Emotn Store / TVBro）
- 安装 `userpack/` 中的用户 APK
- 修复用户应用/应用商店权限
- 关闭 JMGO OTA 更新（可逆）
- 开启 3D 设置
- 重启 Bonfire OS

## 使用方法

### 准备

1. 投影仪开启 **开发者选项 → USB 调试 / 网络 ADB**（无线调试）
2. 电脑安装 [Android SDK Platform Tools](https://developer.android.com/tools/releases/platform-tools)（含 `adb`）
3. 电脑与投影仪在同一局域网，记下投影仪 IP 和 ADB 端口（端口每次重启会变）
4. 连接一次：`adb connect <投影仪IP>:<端口>`，出现授权提示时在投影仪上点"允许"

### 运行

**macOS / Linux：**

```bash
cd jmgo-bonfire-os-tuner
./bonfire_tuner_full.sh <投影仪IP>:<端口>
# 例：./bonfire_tuner_full.sh 192.168.0.30:32909
```

不带参数启动时，工具会自动扫描本机已连接的 ADB 设备。

**Windows：**

```bat
bonfire_tuner_full.bat <投影仪IP>:<端口>
```

**macOS 一键启动（可选）：** 双击 `启动JMGO工具.command`（可拖到 Dock 固定）。它会自动读取上次连接、回退扫描端口，无需手输命令。

进入中文菜单后，输入数字选择功能，按 `A` 依次执行全部任务（每项仍会单独确认），按 `Q` 退出。

## 目录结构

```
.
├── bonfire_tuner_full.py          # 主程序（跨平台 Python，含中文界面层）
├── bonfire_tuner_full.sh          # macOS / Linux 启动脚本
├── bonfire_tuner_full.bat         # Windows 启动脚本
├── 启动JMGO工具.command           # macOS 一键启动器
├── search/                        # Google TV 搜索 + 语音相关 APK
│   ├── BonfireN5SVoiceBridge.apk  # 语音键桥接（本仓库自研，源码见 bridge/）
│   └── com.google.android.katniss*.apk
├── screensaver/AmbientMode.apk    # 屏保相关
├── settings/JmGOSetting-clone.apk # 设置克隆版
├── rupack/                        # RU 插件 APK
├── userpack/                      # 放你想安装的用户 APK（默认空）
└── bridge/                        # 语音桥接 APK 的 Java 源码
```

## 语音键桥接（自研部分）

`bridge/VoiceBridgeService.java` 是本工具箱自研的无障碍服务，解决"输入框内按语音键跳谷歌搜索"的问题：

- 语音键识别：兼容 `keyCode=609`（蓝牙遥控）与 `scanCode=581/155`（红外/底层事件）
- 输入态判定：结合 `InputMethodManager.isAcceptingText()` 与无障碍节点树中的聚焦可编辑控件，兼容 TVBox 等自绘键盘应用
- 输入框内 → 启动搜狗 TV 输入法的语音识别；非输入框 → 打开 Google Katniss 语音搜索

编译需要 Android SDK（build-tools + platform 34），依赖搜狗 TV 输入法 `com.sohu.inputmethod.sogou.tv`。

## 研究记录

想知道这些功能**是怎么研究出来的**、或者想在别的机型上复现/扩展？见 [RESEARCH.md](RESEARCH.md)。里面逐项记录了定位思路和验证方法，包括：

- 语音键桥接的完整逆向过程（反汇编 → 定位真实键码 → 定位输入态判定 → 双场景验证）
- 投屏被误禁用、设置键接管、屏保不生效等问题的排查方法
- 一张「目标 → 方法」的可复用命令速查表
- 自研桥接 APK 的编译流程

## 致谢与说明

- 原始 Bonfire OS Tuner 工具包作者
- Google（Katniss / TV Backdrop）、SmartTube、TVBro、Emotn Store 等应用作者
- `settings/` 与 `screensaver/` 中的部分 APK 提取自 JMGO 原厂固件，版权归 JMGO 所有。本仓库仅用于个人学习与技术交流，**请在下载后 24 小时内删除，勿用于商业用途**。若你是相关权利人并要求下架，请提交 Issue。

## 免责声明

本工具通过 ADB 修改系统设置与应用状态，可能导致设备功能异常或失去保修。使用前请自行备份，**一切后果由使用者自行承担**。本仓库不构成对任何第三方应用或固件的授权、背书或分发许可。

## 协议

[MIT](LICENSE)
