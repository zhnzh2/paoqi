import { useState, useRef, useEffect } from "react";

export interface ChatMessage {
  sender: string;
  color: "R" | "B";
  text: string;
}

type ChatPanelProps = {
  messages: ChatMessage[];
  myColor: "R" | "B" | null;
  onSend: (text: string) => void;
  disabled?: boolean;
};

export default function ChatPanel({
  messages,
  myColor,
  onSend,
  disabled,
}: ChatPanelProps) {
  const [input, setInput] = useState("");
  const listRef = useRef<HTMLDivElement>(null);

  // 新消息自动滚到底部
  useEffect(() => {
    if (listRef.current) {
      listRef.current.scrollTop = listRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSend = () => {
    const text = input.trim();
    if (!text || disabled) return;
    onSend(text);
    setInput("");
  };

  const maxLen = 50;
  const remaining = maxLen - input.length;

  return (
    <div className="chat-panel">
      <div className="chat-panel-title">房间聊天</div>

      <div className="chat-message-list" ref={listRef}>
        {messages.length === 0 ? (
          <div className="chat-empty">暂无消息</div>
        ) : (
          messages.map((msg, i) => (
            <div
              key={i}
              className={`chat-message ${
                msg.color === "R" ? "chat-message-red" : "chat-message-blue"
              }`}
            >
              <span className="chat-message-sender">
                {msg.sender}
                {msg.color === "R" ? " 🔴" : " 🔵"}：
              </span>
              <span className="chat-message-text">{msg.text}</span>
            </div>
          ))
        )}
      </div>

      <div className="chat-input-row">
        <input
          className="chat-input"
          type="text"
          maxLength={maxLen}
          placeholder="输入消息（最多50字）..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") handleSend();
          }}
          disabled={disabled}
        />
        <button
          className="chat-send-button"
          onClick={handleSend}
          disabled={disabled || !input.trim()}
        >
          发送
        </button>
      </div>
      <div className="chat-char-count">
        {remaining}/{maxLen}
      </div>
    </div>
  );
}
