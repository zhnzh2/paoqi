import { useState, type FormEvent } from "react";
import { authApi, type UserProfile } from "../../api/authApi";

interface BasicInfoPanelProps {
  profile: UserProfile;
  isOwner: boolean;
  onProfileUpdated: (profile: UserProfile) => void;
}

export default function BasicInfoPanel({
  profile,
  isOwner,
  onProfileUpdated,
}: BasicInfoPanelProps) {
  const [editingIntro, setEditingIntro] = useState(false);
  const [introText, setIntroText] = useState(profile.intro_letter);
  const [introSaving, setIntroSaving] = useState(false);
  const [introError, setIntroError] = useState("");
  const [introSuccess, setIntroSuccess] = useState("");

  const [showPasswordForm, setShowPasswordForm] = useState(false);
  const [oldPassword, setOldPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [passwordError, setPasswordError] = useState("");
  const [passwordSuccess, setPasswordSuccess] = useState("");
  const [passwordSaving, setPasswordSaving] = useState(false);

  const handleSaveIntro = async (e: FormEvent) => {
    e.preventDefault();
    setIntroError("");
    setIntroSuccess("");
    setIntroSaving(true);

    try {
      const res = await authApi.updateProfile(introText.trim());
      if (res.ok) {
        onProfileUpdated(res.data.user);
        setIntroSuccess("介绍信已更新");
        setEditingIntro(false);
      } else {
        setIntroError(res.message);
      }
    } catch {
      setIntroError("网络错误");
    } finally {
      setIntroSaving(false);
    }
  };

  const handleChangePassword = async (e: FormEvent) => {
    e.preventDefault();
    setPasswordError("");
    setPasswordSuccess("");

    if (!oldPassword) {
      setPasswordError("请输入旧密码");
      return;
    }
    if (!newPassword) {
      setPasswordError("请输入新密码");
      return;
    }

    setPasswordSaving(true);
    try {
      const res = await authApi.changePassword(oldPassword, newPassword);
      if (res.ok) {
        setPasswordSuccess("密码已修改");
        setOldPassword("");
        setNewPassword("");
        setShowPasswordForm(false);
      } else {
        setPasswordError(res.message);
      }
    } catch {
      setPasswordError("网络错误");
    } finally {
      setPasswordSaving(false);
    }
  };

  const registeredDate = profile.registered_at
    ? new Date(profile.registered_at).toLocaleDateString("zh-CN", {
        year: "numeric",
        month: "long",
        day: "numeric",
      })
    : "未知";

  return (
    <div className="user-panel">
      <h2 className="user-panel-title">基本信息</h2>

      {/* 用户信息展示 */}
      <div className="info-grid">
        <div className="info-item">
          <span className="info-label">UID</span>
          <span className="info-value">{profile.uid}</span>
        </div>
        <div className="info-item">
          <span className="info-label">用户名</span>
          <span className="info-value">{profile.username}</span>
        </div>
        <div className="info-item">
          <span className="info-label">角色</span>
          <span className="info-value">{profile.role}</span>
        </div>
        <div className="info-item">
          <span className="info-label">注册时间</span>
          <span className="info-value">{registeredDate}</span>
        </div>
      </div>

      {/* 介绍信 */}
      <div className="info-section">
        <div className="info-section-header">
          <h3 className="info-section-title">介绍信</h3>
          {isOwner && !editingIntro && (
            <button
              className="info-edit-button"
              onClick={() => {
                setIntroText(profile.intro_letter);
                setIntroError("");
                setIntroSuccess("");
                setEditingIntro(true);
              }}
            >
              编辑
            </button>
          )}
        </div>

        {editingIntro ? (
          <form onSubmit={handleSaveIntro} className="info-edit-form">
            <textarea
              className="info-textarea"
              value={introText}
              onChange={(e) => setIntroText(e.target.value)}
              maxLength={500}
              rows={4}
              disabled={introSaving}
            />
            {introError && <div className="info-message info-message-error">{introError}</div>}
            {introSuccess && <div className="info-message info-message-success">{introSuccess}</div>}
            <div className="info-edit-actions">
              <button
                type="submit"
                className="info-save-button"
                disabled={introSaving}
              >
                {introSaving ? "保存中..." : "保存"}
              </button>
              <button
                type="button"
                className="info-cancel-button"
                onClick={() => {
                  setEditingIntro(false);
                  setIntroError("");
                }}
                disabled={introSaving}
              >
                取消
              </button>
            </div>
          </form>
        ) : (
          <p className="info-intro-text">
            {profile.intro_letter || "（未填写）"}
          </p>
        )}
      </div>

      {/* 修改密码（仅本人可见） */}
      {isOwner && (
        <div className="info-section">
          <div className="info-section-header">
            <h3 className="info-section-title">修改密码</h3>
            {!showPasswordForm && (
              <button
                className="info-edit-button"
                onClick={() => {
                  setOldPassword("");
                  setNewPassword("");
                  setPasswordError("");
                  setPasswordSuccess("");
                  setShowPasswordForm(true);
                }}
              >
                修改
              </button>
            )}
          </div>

          {showPasswordForm && (
            <form onSubmit={handleChangePassword} className="info-edit-form">
              <div className="info-field">
                <label className="info-field-label">旧密码</label>
                <input
                  type="password"
                  className="info-input"
                  value={oldPassword}
                  onChange={(e) => setOldPassword(e.target.value)}
                  disabled={passwordSaving}
                  autoComplete="current-password"
                />
              </div>
              <div className="info-field">
                <label className="info-field-label">新密码</label>
                <input
                  type="password"
                  className="info-input"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  disabled={passwordSaving}
                  autoComplete="new-password"
                />
              </div>
              {passwordError && <div className="info-message info-message-error">{passwordError}</div>}
              {passwordSuccess && <div className="info-message info-message-success">{passwordSuccess}</div>}
              <div className="info-edit-actions">
                <button
                  type="submit"
                  className="info-save-button"
                  disabled={passwordSaving}
                >
                  {passwordSaving ? "修改中..." : "确认修改"}
                </button>
                <button
                  type="button"
                  className="info-cancel-button"
                  onClick={() => {
                    setShowPasswordForm(false);
                    setPasswordError("");
                  }}
                  disabled={passwordSaving}
                >
                  取消
                </button>
              </div>
            </form>
          )}
        </div>
      )}
    </div>
  );
}
