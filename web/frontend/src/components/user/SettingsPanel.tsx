import { useState, useEffect, useCallback } from "react";
import { authApi } from "../../api/authApi";

const DEFAULT_SETTINGS: Record<string, boolean> = {
  showRecordPanel: true,
  showCoordInsideCell: false,
  showDropHighlight: true,
  showEatHighlight: true,
  showMuzzleHighlight: true,
  showFireHighlight: true,
  showArrowHints: true,
  showHoverPreview: true,
  showCannonHoverEnhance: true,
  compactSidebar: false,
};

const SETTING_LABELS: Record<string, string> = {
  showRecordPanel: "显示棋谱",
  showCoordInsideCell: "格内显示坐标",
  showDropHighlight: "显示落子 hover 高亮",
  showEatHighlight: "显示吃子高亮",
  showMuzzleHighlight: "显示炮口高亮",
  showFireHighlight: "显示打炮高亮",
  showArrowHints: "显示炮口方向箭头",
  showHoverPreview: "显示 hover 虚化预览",
  showCannonHoverEnhance: "显示炮管 hover 增强高亮",
  compactSidebar: "右栏紧凑模式",
};

const DISPLAY_GROUP: string[] = [
  "showRecordPanel",
  "showCoordInsideCell",
  "compactSidebar",
];

const HIGHLIGHT_GROUP: string[] = [
  "showDropHighlight",
  "showEatHighlight",
  "showMuzzleHighlight",
  "showFireHighlight",
  "showArrowHints",
  "showHoverPreview",
  "showCannonHoverEnhance",
];

interface SettingsPanelProps {
  isOwner: boolean;
}

export default function SettingsPanel({ isOwner }: SettingsPanelProps) {
  const [settings, setSettings] = useState<Record<string, boolean>>(DEFAULT_SETTINGS);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  // 加载设置
  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    authApi
      .getSettings()
      .then((res) => {
        if (cancelled) return;
        if (res.ok) {
          setSettings({ ...DEFAULT_SETTINGS, ...res.data.settings });
        }
      })
      .catch(() => {
        // 使用默认值
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const toggleSetting = useCallback(
    (key: string) => {
      if (!isOwner) return;
      setSettings((prev) => ({ ...prev, [key]: !prev[key] }));
      // 清除之前的消息
      setMessage("");
      setError("");
    },
    [isOwner],
  );

  const handleSave = async () => {
    setSaving(true);
    setMessage("");
    setError("");
    try {
      const res = await authApi.saveSettings(settings);
      if (res.ok) {
        setMessage("设置已保存");
      } else {
        setError(res.message);
      }
    } catch {
      setError("网络错误");
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="user-panel">
        <h2 className="user-panel-title">设置</h2>
        <div className="user-content-loading">加载中...</div>
      </div>
    );
  }

  return (
    <div className="user-panel">
      <h2 className="user-panel-title">设置</h2>
      <p className="user-panel-desc">
        这些设置将作为你开始新对局时的默认选项。
        {!isOwner && "（仅本人可修改）"}
      </p>

      <div className="settings-group">
        <div className="settings-group-title">界面显示</div>
        <div className="settings-list">
          {DISPLAY_GROUP.map((key) => (
            <label key={key} className="settings-item">
              <input
                type="checkbox"
                checked={settings[key] ?? DEFAULT_SETTINGS[key]}
                onChange={() => toggleSetting(key)}
                disabled={!isOwner}
              />
              {SETTING_LABELS[key] ?? key}
            </label>
          ))}
        </div>
      </div>

      <div className="settings-group">
        <div className="settings-group-title">高亮与提示</div>
        <div className="settings-list">
          {HIGHLIGHT_GROUP.map((key) => (
            <label key={key} className="settings-item">
              <input
                type="checkbox"
                checked={settings[key] ?? DEFAULT_SETTINGS[key]}
                onChange={() => toggleSetting(key)}
                disabled={!isOwner}
              />
              {SETTING_LABELS[key] ?? key}
            </label>
          ))}
        </div>
      </div>

      {message && <div className="info-message info-message-success">{message}</div>}
      {error && <div className="info-message info-message-error">{error}</div>}

      {isOwner && (
        <div className="settings-actions">
          <button
            className="info-save-button"
            onClick={handleSave}
            disabled={saving}
          >
            {saving ? "保存中..." : "保存设置"}
          </button>
        </div>
      )}
    </div>
  );
}
