package com.jmgo.tools.voicebridge;

import android.accessibilityservice.AccessibilityService;
import android.content.ComponentName;
import android.content.Intent;
import android.util.Log;
import android.view.KeyEvent;
import android.view.accessibility.AccessibilityEvent;
import android.view.accessibility.AccessibilityNodeInfo;
import android.view.inputmethod.InputMethodManager;

public class VoiceBridgeService extends AccessibilityService {
    private static final String TAG = "BonfireVoiceBridge";
    private static final int KEY_VOICE = 609;
    // 真机实测：遥控语音键 keyCode=609 或 0，靠 scanCode 兜底（红外 581 / 蓝牙 155）
    private static final int SCAN_IR_VOICE = 581;
    private static final int SCAN_BT_VOICE = 155;
    private static final ComponentName SOGOU_KEYBOARD_STATE = new ComponentName(
            "com.sohu.inputmethod.sogou.tv",
            "com.sogou.speech.keyboardstate.KeyboardStateService");
    private static final String SOGOU_START =
            "com.sohu.inputmethod.sogou.tv.VOICE_BRIDGE_START_73B8380D";
    private static final String SOGOU_STOP =
            "com.sohu.inputmethod.sogou.tv.VOICE_BRIDGE_STOP_73B8380D";

    private boolean sogouVoiceActive = false;

    @Override
    protected void onServiceConnected() {
        super.onServiceConnected();
        Log.i(TAG, "VoiceBridgeService connected");
    }

    @Override
    public void onAccessibilityEvent(AccessibilityEvent event) { }

    @Override
    public void onInterrupt() {
        stopSogouVoice();
    }

    @Override
    protected boolean onKeyEvent(KeyEvent event) {
        int kc = event.getKeyCode();
        int sc = event.getScanCode();
        boolean isVoice = (kc == KEY_VOICE) || (sc == SCAN_IR_VOICE) || (sc == SCAN_BT_VOICE);
        if (!isVoice) {
            return false;
        }
        boolean input = isTextInputActive();
        Log.i(TAG, "VOICE key=" + kc + " scan=" + sc + " action=" + event.getAction()
                + " input=" + input);

        if (event.getAction() == KeyEvent.ACTION_DOWN && event.getRepeatCount() == 0) {
            if (input) {
                startSogouVoice();
            } else {
                openKatnissSearch();
            }
        } else if (event.getAction() == KeyEvent.ACTION_UP) {
            stopSogouVoice();
        }
        return false;
    }

    /**
     * 判定当前是否处于“正在输入文字”。
     * 1) 系统 IME 正在接受文本（如搜狗/原生键盘弹出）
     * 2) 焦点窗口内存在 focused 且可编辑的 EditText（覆盖 TVBox 这类自绘键盘，
     *    它们焦点在 EditText 上但 mServedView=null，isAcceptingText() 为 false）
     */
    private boolean isTextInputActive() {
        // 1) 系统 IME
        try {
            InputMethodManager imm =
                    (InputMethodManager) getSystemService(INPUT_METHOD_SERVICE);
            if (imm != null && imm.isAcceptingText()) {
                return true;
            }
        } catch (Throwable t) {
            Log.w(TAG, "isAcceptingText failed", t);
        }
        // 2) 无障碍节点树：找 focused + editable 节点
        try {
            AccessibilityNodeInfo root = getRootInActiveWindow();
            if (root != null && hasFocusedEditable(root)) {
                return true;
            }
        } catch (Throwable t) {
            Log.w(TAG, "a11y node scan failed", t);
        }
        return false;
    }

    private boolean hasFocusedEditable(AccessibilityNodeInfo node) {
        if (node == null) {
            return false;
        }
        try {
            if (node.isFocused() && node.isEditable()) {
                return true;
            }
            int count = node.getChildCount();
            for (int i = 0; i < count; i++) {
                AccessibilityNodeInfo child = node.getChild(i);
                if (child != null) {
                    try {
                        if (hasFocusedEditable(child)) {
                            return true;
                        }
                    } finally {
                        child.recycle();
                    }
                }
            }
        } catch (Throwable t) {
            Log.w(TAG, "node traverse failed", t);
        }
        return false;
    }

    private void startSogouVoice() {
        try {
            Intent intent = new Intent(SOGOU_START);
            intent.setComponent(SOGOU_KEYBOARD_STATE);
            startService(intent);
            sogouVoiceActive = true;
            Log.i(TAG, "IME active -> Sogou voice START");
        } catch (Throwable t) {
            Log.w(TAG, "Could not start Sogou voice input", t);
            sogouVoiceActive = false;
        }
    }

    private void stopSogouVoice() {
        if (!sogouVoiceActive) {
            return;
        }
        try {
            Intent intent = new Intent(SOGOU_STOP);
            intent.setComponent(SOGOU_KEYBOARD_STATE);
            startService(intent);
        } catch (Throwable t) {
            Log.w(TAG, "Could not stop Sogou voice input", t);
        }
        sogouVoiceActive = false;
    }

    private void openKatnissSearch() {
        try {
            Intent intent = new Intent("android.speech.action.WEB_SEARCH");
            intent.setPackage("com.google.android.katniss");
            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            startActivity(intent);
            Log.i(TAG, "No IME -> Katniss search");
        } catch (Throwable t) {
            Log.w(TAG, "Could not open Katniss voice search", t);
        }
    }
}
