type RoomInfoPanelProps = {
  roomCode: string;
  redName: string | null;
  blueName: string | null;
  redConnected: boolean;
  blueConnected: boolean;
  myColor: "R" | "B" | null;
  isMyTurn?: boolean;
  phase?: string;
  isConnected?: boolean;
};

export default function RoomInfoPanel({
  roomCode,
  redName,
  blueName,
  redConnected,
  blueConnected,
  myColor,
  isMyTurn,
  phase,
  isConnected,
}: RoomInfoPanelProps) {
  const handleCopyCode = () => {
    navigator.clipboard.writeText(roomCode);
  };

  return (
    <div className="room-info-panel">
      <div className="room-info-panel-title">房间信息</div>

      <div className="room-info-item">
        <span className="room-info-label">房间码</span>
        <span
          className="room-info-code-value"
          onClick={handleCopyCode}
          title="点击复制"
        >
          {roomCode}
        </span>
      </div>

      {phase === "playing" && (
        <div className="room-info-item">
          <span className="room-info-label">当前回合</span>
          <span
            className={`room-info-value ${isMyTurn ? "room-info-turn-mine" : "room-info-turn-opponent"}`}
          >
            {isMyTurn ? "你的回合" : "对手回合"}
          </span>
        </div>
      )}

      {isConnected === false && (
        <div className="room-info-item">
          <span className="room-info-label">连接状态</span>
          <span className="room-info-status room-info-status-offline">
            已断开
          </span>
        </div>
      )}

      <div className="room-info-item">
        <span className="room-info-label">🔴 红方</span>
        <span className="room-info-value">
          {redName
            ? `${redName}${myColor === "R" ? "（你）" : ""}`
            : "等待中"}
          {redName && (
            <span
              className={`room-info-status ${
                redConnected
                  ? "room-info-status-online"
                  : "room-info-status-offline"
              }`}
            >
              {redConnected ? "在线" : "离线"}
            </span>
          )}
        </span>
      </div>

      <div className="room-info-item">
        <span className="room-info-label">🔵 蓝方</span>
        <span className="room-info-value">
          {blueName
            ? `${blueName}${myColor === "B" ? "（你）" : ""}`
            : "等待中"}
          {blueName && (
            <span
              className={`room-info-status ${
                blueConnected
                  ? "room-info-status-online"
                  : "room-info-status-offline"
              }`}
            >
              {blueConnected ? "在线" : "离线"}
            </span>
          )}
        </span>
      </div>
    </div>
  );
}
