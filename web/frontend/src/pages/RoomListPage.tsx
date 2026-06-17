import { useEffect, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import UserBar from "../components/layout/UserBar";
import { createRoom, listRooms, type RoomInfo } from "../api/roomApi";

export default function RoomListPage() {
  const navigate = useNavigate();
  const [rooms, setRooms] = useState<RoomInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [joinCode, setJoinCode] = useState("");
  const [creating, setCreating] = useState(false);

  const fetchRooms = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await listRooms();
      if (res.ok && res.data?.rooms) {
        setRooms(res.data.rooms);
      } else {
        setError(res.message ?? "获取房间列表失败");
      }
    } catch {
      setError("网络错误，无法获取房间列表");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchRooms();
    // 每 5 秒刷新一次
    const interval = setInterval(fetchRooms, 5000);
    return () => clearInterval(interval);
  }, [fetchRooms]);

  const handleCreateRoom = async () => {
    setCreating(true);
    setError(null);
    try {
      const res = await createRoom();
      if (res.ok && res.data?.room_code) {
        navigate(`/room/${res.data.room_code}`);
      } else {
        setError(res.message ?? "创建房间失败");
      }
    } catch {
      setError("网络错误，无法创建房间");
    } finally {
      setCreating(false);
    }
  };

  const handleJoinByCode = () => {
    const code = joinCode.trim().toUpperCase();
    if (code.length !== 6) {
      setError("请输入 6 位房间码");
      return;
    }
    navigate(`/room/${code}`);
  };

  const handleJoinRoom = (code: string) => {
    navigate(`/room/${code}`);
  };

  return (
    <div className="room-selection-page">
      <UserBar />

      <div className="room-selection-header">
        <h1>联机对战</h1>
        <p>创建或加入一个房间，与好友实时对弈</p>
      </div>

      {error ? (
        <div className="room-error">{error}</div>
      ) : null}

      <div className="room-grid">
        {/* 左侧：创建房间 */}
        <div className="room-card room-card-create">
          <h2>创建房间</h2>
          <p>
            创建一个新房间，将房间码分享给好友即可开始对局。
            你将为<strong>红方</strong>，先手行棋。
          </p>
          <button
            className="room-card-button room-card-button-primary"
            onClick={handleCreateRoom}
            disabled={creating}
          >
            {creating ? "创建中..." : "创建房间"}
          </button>
        </div>

        {/* 右侧：加入房间 */}
        <div className="room-card room-card-join">
          <h2>加入房间</h2>

          {/* 输入房间码加入 */}
          <div className="join-by-code">
            <label className="join-code-label">输入房间码加入</label>
            <div className="join-code-row">
              <input
                className="join-code-input"
                type="text"
                maxLength={6}
                placeholder="例如: EHD56I"
                value={joinCode}
                onChange={(e) => setJoinCode(e.target.value.toUpperCase())}
                onKeyDown={(e) => {
                  if (e.key === "Enter") handleJoinByCode();
                }}
              />
              <button
                className="room-card-button room-card-button-primary"
                onClick={handleJoinByCode}
              >
                加入
              </button>
            </div>
          </div>

          {/* 可用房间列表 */}
          <div className="room-list-section">
            <label className="join-code-label">
              可用房间
              <button
                className="room-refresh-button"
                onClick={fetchRooms}
                disabled={loading}
                title="刷新"
              >
                {loading ? "刷新中..." : "刷新"}
              </button>
            </label>

            {loading && rooms.length === 0 ? (
              <div className="room-list-empty">加载中...</div>
            ) : rooms.length === 0 ? (
              <div className="room-list-empty">
                暂无可用房间，请创建一个新房间
              </div>
            ) : (
              <div className="room-list">
                {rooms.map((room) => (
                  <div key={room.code} className="room-list-item">
                    <div className="room-list-item-info">
                      <span className="room-list-code">{room.code}</span>
                      <span className="room-list-players">
                        {room.red_username}
                        {room.player_count === 2
                          ? " vs ?"
                          : " (等待中)"}
                      </span>
                      <span className="room-list-count">
                        {room.player_count}/2 人
                      </span>
                    </div>
                    <button
                      className="room-list-join-button"
                      onClick={() => handleJoinRoom(room.code)}
                      disabled={room.player_count >= 2}
                    >
                      {room.player_count >= 2 ? "已满" : "加入"}
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      <button
        className="room-back-button"
        onClick={() => navigate("/")}
      >
        返回主菜单
      </button>
    </div>
  );
}
