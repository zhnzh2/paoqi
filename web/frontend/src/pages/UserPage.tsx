import { useState, useEffect } from "react";
import { useParams, useNavigate, Navigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { authApi, type UserProfile } from "../api/authApi";
import BasicInfoPanel from "../components/user/BasicInfoPanel";
import SettingsPanel from "../components/user/SettingsPanel";
import RecordListPanel from "../components/user/RecordListPanel";

type PanelKey = "info" | "settings" | "records";

export default function UserPage() {
  const { uid: uidStr } = useParams<{ uid: string }>();
  const uid = Number(uidStr);
  const navigate = useNavigate();
  const { user: currentUser, isAuthenticated, isAuthLoading } = useAuth();

  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [activePanel, setActivePanel] = useState<PanelKey>("info");
  const isOwner = currentUser?.uid === uid;

  // 加载目标用户的 profile
  useEffect(() => {
    if (!uid || isNaN(uid)) return;

    let cancelled = false;
    setLoading(true);
    setError("");

    authApi
      .getUserProfile(uid)
      .then((res) => {
        if (cancelled) return;
        if (res.ok) {
          setProfile(res.data.user);
        } else {
          setError(res.message);
        }
      })
      .catch(() => {
        if (!cancelled) setError("网络错误");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [uid]);

  useEffect(() => {
    if (!isOwner && activePanel === "records") {
      setActivePanel("info");
    }
  }, [activePanel, isOwner]);

  // 检查登录
  if (isAuthLoading) {
    return (
      <div className="page" style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100vh", color: "#ccc" }}>
        加载中...
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  const panelLabels: Record<PanelKey, string> = {
    info: "基本信息",
    settings: "设置",
    records: "历史对局",
  };
  const visiblePanels = (Object.keys(panelLabels) as PanelKey[]).filter(
    (key) => key !== "records" || isOwner,
  );

  return (
    <div className="user-page">
      {/* 左侧导航栏 */}
      <div className="user-sidebar">
        <div className="user-sidebar-header">
          <button
            className="user-back-button"
            onClick={() => navigate("/")}
          >
            ← 返回
          </button>
        </div>

        <div className="user-sidebar-avatar">
          <div className="user-avatar-circle">
            {(profile?.username ?? "?").charAt(0).toUpperCase()}
          </div>
          <div className="user-sidebar-name">{profile?.username ?? "加载中..."}</div>
          {profile?.role ? (
            <div
              className={`user-sidebar-role ${profile.role === "站主" ? "user-sidebar-role-owner" : profile.role === "管理员" ? "user-sidebar-role-admin" : ""}`}
            >
              {profile.role}
            </div>
          ) : null}
        </div>

        <nav className="user-sidebar-nav">
          {visiblePanels.map((key) => (
            <button
              key={key}
              className={`user-nav-item ${activePanel === key ? "user-nav-item-active" : ""}`}
              onClick={() => setActivePanel(key)}
            >
              {panelLabels[key]}
            </button>
          ))}
        </nav>
      </div>

      {/* 右侧内容区 */}
      <div className="user-content">
        {loading ? (
          <div className="user-content-loading">加载中...</div>
        ) : error ? (
          <div className="user-content-error">{error}</div>
        ) : profile ? (
          activePanel === "info" ? (
            <BasicInfoPanel
              profile={profile}
              isOwner={isOwner}
              onProfileUpdated={setProfile}
            />
          ) : activePanel === "records" ? (
            <RecordListPanel uid={uid} />
          ) : (
            <SettingsPanel isOwner={isOwner} />
          )
        ) : null}
      </div>
    </div>
  );
}
