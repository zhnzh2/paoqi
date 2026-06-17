import { useNavigate } from "react-router-dom";

type ComingSoonPageProps = {
  mode: string;
};

export default function ComingSoonPage({ mode }: ComingSoonPageProps) {
  const navigate = useNavigate();

  return (
    <div className="menu-page">
      <div className="menu-card" style={{ textAlign: "center" }}>
        <div className="menu-title" style={{ fontSize: "42px", marginBottom: "16px" }}>
          {mode}
        </div>
        <p style={{ color: "#888", fontSize: "18px", marginBottom: "28px" }}>
          🚧 该模式正在开发中，敬请期待。
        </p>
        <button
          className="menu-button menu-button-secondary"
          style={{ width: "180px", minHeight: "48px", fontSize: "16px" }}
          onClick={() => navigate("/")}
        >
          返回主菜单
        </button>
      </div>
    </div>
  );
}
