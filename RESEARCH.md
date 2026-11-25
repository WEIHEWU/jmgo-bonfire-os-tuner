# 研究记录：JMGO Bonfire OS 定制过程

本文档记录本工具箱各项功能**是如何研究出来的**——遇到问题时的定位思路、用到的命令、以及验证方法。目的是让其他人能够复现、修改或扩展这些研究，而不只是拿到一个黑盒工具。

> 适用设备：JMGO N5 Ultra（机型 `K941CN`，device/name `K931CN`，Android 14，Bonfire OS，设置版本 8.1.959）。
> 研究方法具有通用性，换机型时按相同思路重新取值即可。

---

## 0. 通用前置：ADB 连接与端口发现

JMGO 的网络 ADB 端口**每次重启都会变**（实测依次出现过 `43719` → `32909` 等），且开发者选项里的无线调试通常是临时开启的。

```bash
# 连接
adb connect 192.168.0.30:<端口>

# 确认是目标设备
adb -s 192.168.0.30:<端口> shell getprop ro.product.model   # K941CN
```

**排查经验**：
- `Connection refused` = 设备端 ADB 服务没在监听，需重新开启无线调试，不要盲目扫端口。
- TCP 能连通 ≠ ADB 可用：实测 `34151` 是 Jetty HTTP 服务，`34927/37189/42493` 握手失败。判断 ADB 端口要发真正的 `CNXN` 握手包，而不是只看 TCP 是否开放。
- 本工具的一键启动器采用三级回退：当前 adb 已连接端口 → 上次成功且仍可连通的缓存端口 → 全端口 ADB 握手扫描。

---

## 1. 语音键桥接：从"总跳谷歌搜索"到"输入框内语音打字"

这是研究最深的一项，完整走了一遍「现象 → 反汇编 → 定位键码 → 定位输入态 → 双场景验证」。

### 1.1 现象

用户反馈：只要按遥控器语音键，就一定弹谷歌搜索，而不是在输入法里做语音输入。

### 1.2 反汇编原桥接 APK，确认行为

把 `search/BonfireN5SVoiceBridge.apk` 解包，用 Android SDK 的 `dexdump` 反汇编无障碍服务：

```bash
unzip -q BonfireN5SVoiceBridge.apk -d /tmp/vb
# 用 build-tools 里的 dexdump
<sdk>/build-tools/36.0.0/dexdump -d /tmp/vb/classes.dex | grep -A 90 'onKeyEvent'
```

**发现**：原服务只判断 `keyCode == 609`，命中就无条件发 `android.speech.action.WEB_SEARCH` 并指定 `com.google.android.katniss`——完全不判断当前是否在输入框里。这就是"按语音键必弹谷歌"的根因。

同时反汇编搜狗 TV 输入法（从设备拉取 `base.apk`）确认它自带语音输入能力：

```bash
adb shell pm path com.sohu.inputmethod.sogou.tv
adb pull <上一步路径> /tmp/sogou.apk
<sdk>/build-tools/36.0.0/dexdump -d classes.dex > /tmp/sogou_dex.txt
grep -n 'VOICE_BRIDGE' /tmp/sogou_dex.txt
```

找到搜狗的私有广播：`com.sohu.inputmethod.sogou.tv.VOICE_BRIDGE_START_73B8380D` / `..._STOP_73B8380D`，指向 `com.sogou.speech.keyboardstate.KeyboardStateService`——这是启动搜狗语音输入的入口。

### 1.3 定位真实按键编码（关键坑）

一开始用 `input keyevent 609` 测试，无障碍服务完全收不到日志。原因：**注入式按键会绕过无障碍按键过滤**，必须用底层事件模拟真实遥控器。

```bash
# 列出输入设备，找到红外遥控器节点
adb shell getevent -il | grep -E 'add device|name:'

# 解析该设备的键码表，算出语音键的 scanCode
adb shell getevent -il /dev/input/event2 > /tmp/ev.txt
# 用脚本从 "KEY (0001):" 段按位置累加，定位 KEY_VOICECOMMAND 的扫描码
# 实测：红外 event2 = 581，蓝牙 event7 = 155

# 用 sendevent 模拟真实按下（DOWN → 同步 → UP → 同步）
adb shell 'sendevent /dev/input/event2 1 581 1; sendevent /dev/input/event2 0 0 0; \
           sendevent /dev/input/event2 1 581 0; sendevent /dev/input/event2 0 0 0'
```

**决定性发现**：真实红外语音键到达无障碍服务时是 `keyCode=0 / scanCode=581`（底层），而真实蓝牙遥控器按键是 `keyCode=609 / scanCode=255`。所以判定条件必须同时覆盖 `keyCode` 和 `scanCode`，否则一半场景识别不到。

### 1.4 定位"是否在输入状态"（第二个关键坑）

第一版改造用 `InputMethodManager.isAcceptingText()` 判断是否在输入框，结果仍失败。抓取 TVBox 搜索页界面结构：

```bash
adb shell uiautomator dump /sdcard/cur.xml
adb shell 'cat /sdcard/cur.xml' | tr '>' '>\n' | grep -iE 'EditText|focused="true"'
adb shell 'dumpsys input_method | grep mServedView=; dumpsys input_method | grep isActive'
```

**发现**：TVBox 搜索框是标准 `android.widget.EditText`（`etSearch`，`focused=true`），但它用**自绘键盘**，`mServedView=null`、`isActive=false`，所以 `isAcceptingText()` 永远是 `false`。

正确判定：**读无障碍节点树里有没有 `focused && editable` 的节点**。需要在配置里开启 `android:canRetrieveWindowContent="true"`，然后递归遍历 `getRootInActiveWindow()`。

### 1.5 最终逻辑与双场景验证

最终服务逻辑（`bridge/VoiceBridgeService.java`）：

- 语音键识别：`keyCode == 609` 或 `scanCode ∈ {581, 155}`
- 输入态判定：`isAcceptingText()` **或** 无障碍节点树中 focused+editable 节点
- 输入态 → 启动搜狗语音识别，识别文字直接填入输入框
- 非输入态 → 打开 Google Katniss 语音搜索

验证方法（读日志 + 截图）：

```bash
adb logcat -c
# 按语音键后
adb logcat -d | grep -i BonfireVoiceBridge
adb exec-out screencap -p > /tmp/shot.png
```

真机双场景结果：

| 场景 | 日志 | 结果 |
|---|---|---|
| TVBox 输入框内按语音键 | `VOICE key=609 scan=255 input=true` → `Sogou voice START` | 识别文字填入搜索框 ✅ |
| 桌面/非输入框按语音键 | `No IME -> Katniss search` | 弹谷歌搜索 ✅ |

**可复用经验**：改造遥控键行为时，先反汇编现有拦截器确认它"认什么键、做什么事"，再用 `sendevent` 而不是 `input keyevent` 做按键测试，最后用 `uiautomator dump` 确认界面真实结构——不要凭 App 类型猜它是否用系统输入法。

---

## 2. 投屏被误禁用：从现象到自愈

用户反馈按"禁用中文应用"后投屏不能用了。

**定位**：检查脚本的 `removable_pkgs` 列表，发现包含了 `com.jmgo.holacast.x`（投屏应用）。用户此前被隐藏过该包，导致投屏失效。

**修复**：
1. 从禁用列表移除 `com.jmgo.holacast.x`
2. 加自愈逻辑：如果发现它已被隐藏，执行 `cmd package install-existing com.jmgo.holacast.x` 恢复

```bash
# 检查某个包是否被隐藏（--user 0 卸载后）
adb shell pm list packages com.jmgo.holacast.x     # 无输出 = 被隐藏
adb shell cmd package install-existing com.jmgo.holacast.x   # 恢复
```

**经验**：批量禁用系统应用时，逐项确认包名对应的真实功能，别按名字里的"中文"字样一刀切。

---

## 3. 设置键接管：为什么不能用"禁用原厂设置"

用户最初想把"设置克隆版"设为默认。尝试 `pm uninstall --user 0 com.jmgo.setting.x`（隐藏原厂设置）被用户纠正：要的是"通过物理设置键打开克隆版"，不是禁用原厂。

**研究过程**：
- 物理设置键的 keycode 是 `605`
- 克隆版自带无障碍服务 `com.jmgo.setting.clone/...SettingsButtonAccessibilityService`，能拦截该键
- 启用服务的广播（注意参数名 `compontentNameStr` 是 App 里的拼写，别改成 `componentNameStr`）：

```bash
adb shell am broadcast --user 0 \
  -a action.jmgo.request.accessibility.service \
  --es compontentNameStr com.jmgo.setting.clone/com.jmgo.setting.recovery.SettingsButtonAccessibilityService \
  --ez enabled true
```

**发现的坑**：仅启用服务后按设置键仍打开原厂菜单。日志显示克隆版捕获了 `SHORT 605`，但模式键 `settings_short_605_mode` 存在私有 SharedPreferences 里，无 root、非 debuggable 无法直接改。最终通过打开克隆版设置界面、用 `input tap` 点选"完整菜单"绑定。

**结论写入工具**：只启用拦截服务，模式由用户在界面上点选，不隐藏原厂设置。

---

## 4. Google 屏保不生效：三个开关 + 熄屏超时

用户反馈装了 Google 屏保但不生效。检查设备设置：

```bash
adb shell 'settings get secure screensaver_enabled; \
           settings get secure screensaver_activate_on_sleep; \
           settings get secure screensaver_activate_on_dock; \
           settings get secure screensaver_components; \
           settings get system screen_off_timeout; \
           settings get global stay_on_while_plugged_in'
```

**根因**：`screensaver_enabled=0`、`screensaver_activate_on_sleep=0`，且 `screen_off_timeout=2147483647`（约 24 天＝永不熄屏）。装了 APK 不等于启用，几个开关都得打开，且屏幕必须能超时才会触发屏保。

**修复**（写入工具第 3 项）：

```bash
adb shell settings put secure screensaver_components \
  com.google.android.apps.tv.dreamx/com.google.android.apps.tv.dreamx.service.Backdrop
adb shell settings put secure screensaver_enabled 1
adb shell settings put secure screensaver_activate_on_sleep 1
adb shell settings put secure screensaver_activate_on_dock 1
adb shell settings put system screen_off_timeout 300000   # 5 分钟
adb shell settings put global stay_on_while_plugged_in 0
```

**验证方法**：先设成 1 分钟 (`60000`) 真机确认屏保出现，再改成 5 分钟定稿。

---

## 5. RU 插件精简与安装冲突

按真机实际安装情况把 `rupack/` 从十几个 APK 精简到 3 个：SmartTube、Emotn Store、TVBro。删除 NUM / projectMTV / TorrServe / RuStore TV。

**安装冲突的判读**（第 6 项日志里常见，属正常，不用修）：
- Emotn Store：签名不匹配（系统预装版与包内版签名不同）
- SmartTube / TVBro：包内版本低于已装版本，Android 拒绝降级

**经验**：`adb install` 报 `INSTALL_FAILED_VERSION_DOWNGRADE` 或签名冲突时，说明设备上已有该应用，是预期行为，不是工具坏了。

---

## 6. 研究方法总结（可复用清单）

| 目标 | 方法 |
|---|---|
| 知道某个系统应用能干什么 | `adb shell dumpsys package <pkg>` 看组件；拉取 `base.apk` 用 `dexdump` 反汇编 |
| 知道遥控器某键发什么码 | `getevent -il` 列设备 + 解析键码表算 scanCode；`sendevent` 模拟真实按键 |
| 测无障碍/按键拦截行为 | 用 `sendevent`，不要用 `input keyevent`（注入键会绕过无障碍过滤） |
| 看界面真实结构 | `uiautomator dump` + `tr '>' '>\n'` 拆节点；不要凭应用类型猜 |
| 确认输入框是否真的走系统 IME | `dumpsys input_method` 看 `mServedView=` 和 `isActive` |
| 查系统设置为什么没生效 | `settings get secure/system/global <key>` 逐项对照 |
| 判断包是否被隐藏 | `pm list packages <pkg>` 无输出即被 `--user 0` 卸载，用 `install-existing` 恢复 |
| 验证改动 | `logcat -c` 清日志 → 操作 → `logcat -d | grep <TAG>` + `screencap` 截图 |

---

## 7. 编译与验证环境

- Android SDK build-tools 36.0.0（`aapt2` / `d8` / `apksigner` / `zipalign` / `dexdump`）
- platform android-34（`android.jar`）
- JDK（Android Studio 自带 JBR 即可）
- 自研桥接源码在 `bridge/`，改完按如下流程重编：

```bash
aapt2 compile --dir res -o compiled.flata
aapt2 link -o unsigned.apk -I android.jar --manifest AndroidManifest.xml \
  compiled.flata --java gen --min-sdk-version 21 --target-sdk-version 28
javac -source 8 -target 8 -classpath android.jar -d classes <源文件>
d8 --lib android.jar --output dexout classes/**/*.class
cp dexout/classes.dex . && zip -q -u unsigned.apk classes.dex
zipalign -f 4 unsigned.apk aligned.apk
apksigner sign --ks debug.jks --ks-pass pass:android \
  --key-pass pass:android --out BonfireN5SVoiceBridge.apk aligned.apk
```

> 注意：APK 用自签名（debug key），重装时需 `adb install -r`。若签名与已装版本冲突，先 `pm uninstall --user 0 com.jmgo.tools.voicebridge` 再装。

---

研究过程中发现的具体坑和取舍以本文档为准；工具本身的使用说明见 [README](README.md)。
