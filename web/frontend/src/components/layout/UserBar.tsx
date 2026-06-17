import { useNavigate } from "react-router-dom";
import { useAuth } from "../../auth/AuthContext";

export default function UserBar() {
  const navigate = useNavigate();
  const { user, logout } = useAuth();

  const handleLogout = async () => {
    await logout();
    navigate("/login", { replace: true });
  };

  return (
    <div className="user-bar">
      <span className="user-bar-info">
        <button
          className="user-bar-name user-bar-name-link"
          onClick={() => user && navigate(`/user/${user.uid}`)}
        >
          {user?.username ?? "未知用户"}
        </button>
        {user?.role && user.role !== "用户" ? (
          <span
            className={`user-bar-role user-bar-role-${
              user.role === "站主" ? "owner" : "admin"
            }`}
          >
            {user.role}
          </span>
        ) : null}
      </span>
      <button className="user-bar-logout" onClick={handleLogout}>
        退出登录
      </button>
    </div>
  );
}
