import { useState, useCallback } from "react";
import type { GamePayload, PlayerColor } from "../../types/game";
import type { ChatMessage } from "../../components/room/ChatPanel";

export type RoomPhase = "waiting" | "playing" | "gameover";

export interface OpponentInfo {
  uid: number;
  username: string;
  color: PlayerColor;
}

export interface RoomGameState {
  payload: GamePayload | null;
  playerColor: PlayerColor | null;
  opponent: OpponentInfo | null;
  opponentConnected: boolean;
  phase: RoomPhase;
  statusMessage: string;
  statusIsError: boolean;
  roomCode: string;
}

export default function useRoomGameState(): RoomGameState & {
  handleWsMessage: (data: any) => void;
  setStatusMessage: (msg: string) => void;
  setStatusIsError: (err: boolean) => void;
  chatMessages: ChatMessage[];
} {
  const [payload, setPayload] = useState<GamePayload | null>(null);
  const [playerColor, setPlayerColor] = useState<PlayerColor | null>(null);
  const [opponent, setOpponent] = useState<OpponentInfo | null>(null);
  const [opponentConnected, setOpponentConnected] = useState(true);
  const [phase, setPhase] = useState<RoomPhase>("waiting");
  const [statusMessage, setStatusMessage] = useState("正在连接房间...");
  const [statusIsError, setStatusIsError] = useState(false);
  const [roomCode, setRoomCode] = useState("");
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);

  const handleWsMessage = useCallback((data: any) => {
    if (!data || typeof data !== "object") return;

    switch (data.type) {
      case "room:waiting_opponent":
        setPlayerColor(data.color ?? "R");
        setRoomCode(data.room_code ?? "");
        setPhase("waiting");
        setStatusMessage(
          `等待对手加入... 房间码: ${data.room_code ?? ""}`,
        );
        setStatusIsError(false);
        break;

      case "room:joined":
        setPlayerColor(data.color ?? "R");
        setRoomCode(data.room_code ?? "");
        if (data.players) {
          const myColor = data.color;
          const opp = (data.players as any[]).find(
            (p: any) => p.color !== myColor,
          );
          if (opp) {
            setOpponent({
              uid: opp.uid,
              username: opp.username,
              color: opp.color,
            });
            setOpponentConnected(opp.connected !== false);
          }
        }
        if (data.payload) {
          setPayload(data.payload);
          setPhase(data.payload.game_over ? "gameover" : "playing");
        }
        setStatusMessage("对局开始！");
        setStatusIsError(false);
        break;

      case "room:player_joined":
        if (data.player) {
          setOpponent({
            uid: data.player.uid,
            username: data.player.username,
            color: data.player.color,
          });
          setOpponentConnected(true);
          setStatusMessage("对手已加入，对局开始！");
          setStatusIsError(false);
        }
        break;

      case "room:player_left":
        setOpponentConnected(false);
        setStatusMessage("对手已离开房间");
        setStatusIsError(true);
        break;

      case "game:state":
        if (data.payload) {
          setPayload(data.payload);
          setPhase(data.payload.game_over ? "gameover" : "playing");
          if (data.payload.game_over) {
            const winner = data.payload.winner;
            const reason = data.payload.game_over_reason ?? "";
            if (winner) {
              const isMe =
                (winner === "R" && playerColor === "R") ||
                (winner === "B" && playerColor === "B");
              setStatusMessage(
                isMe
                  ? `对局结束，你赢了！${reason}`
                  : `对局结束，你输了。${reason}`,
              );
            } else {
              setStatusMessage(`对局结束：${reason}`);
            }
            setStatusIsError(false);
          } else {
            setStatusMessage("");
            setStatusIsError(false);
          }
        }
        break;

      case "game:error":
        setStatusMessage(data.message ?? "操作失败");
        setStatusIsError(true);
        break;

      case "opponent:disconnected":
        setOpponentConnected(false);
        setStatusMessage("对手已断开连接，等待重连...");
        setStatusIsError(true);
        break;

      case "opponent:reconnected":
        setOpponentConnected(true);
        setStatusMessage("对手已重新连接");
        setStatusIsError(false);
        break;

      case "game:restarted":
        if (data.payload) {
          setPayload(data.payload);
          setPhase("playing");
        }
        if (data.players && playerColor) {
          const nextColor: PlayerColor =
            playerColor === "R" ? "B" : "R";
          setPlayerColor(nextColor);
          const opp = (data.players as any[]).find(
            (p: any) => p.color !== nextColor,
          );
          if (opp) {
            setOpponent({
              uid: opp.uid,
              username: opp.username,
              color: opp.color,
            });
            setOpponentConnected(opp.connected !== false);
          }
        }
        setChatMessages([]);
        setStatusMessage("新一局开始！");
        setStatusIsError(false);
        break;

      case "chat:message":
        setChatMessages((prev) => [
          ...prev,
          {
            sender: data.sender ?? "?",
            color: data.color ?? "R",
            text: data.text ?? "",
          },
        ]);
        break;

      default:
        break;
    }
  }, [playerColor]);

  return {
    payload,
    playerColor,
    opponent,
    opponentConnected,
    phase,
    statusMessage,
    statusIsError,
    roomCode,
    handleWsMessage,
    setStatusMessage,
    setStatusIsError,
    chatMessages,
  };
}
