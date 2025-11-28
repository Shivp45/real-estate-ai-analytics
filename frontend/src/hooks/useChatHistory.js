import { useEffect, useState } from "react";

export function useChatHistory(userId) {
  const storageKey = userId ? `chat_history_${userId}` : "chat_history_guest";

  const [messages, setMessages] = useState(() => {
    try {
      const saved = localStorage.getItem(storageKey);
      return saved ? JSON.parse(saved) : [];
    } catch {
      return [];
    }
  });

  // Auto-save messages to localStorage when they change
  useEffect(() => {
    if (!userId) return;
    localStorage.setItem(storageKey, JSON.stringify(messages));
  }, [messages, userId]);

  // When user logs out or switches account → load correct history
  useEffect(() => {
    if (!userId) return;

    const saved = localStorage.getItem(storageKey);
    setMessages(saved ? JSON.parse(saved) : []);
  }, [userId]);

  const addUserMessage = (text) => {
    setMessages((prev) => [
      ...prev,
      { id: Date.now(), type: "user", message: text },
    ]);
  };

  const addBotMessage = (response) => {
  const normalized = {
    id: Date.now(),
    type: "bot",
    summary: response?.summary ?? response?.data?.summary ?? "⚠️ No AI summary",
    charts: response?.charts ?? response?.data?.charts ?? [],
    table: response?.table ?? response?.data?.table ?? { columns: [], rows: [] }
  };

  setMessages((prev) => {
    const updated = [...prev, normalized];
    localStorage.setItem(storageKey, JSON.stringify(updated));
    return updated;
  });
};


  const clearChat = () => {
    localStorage.removeItem(storageKey);
    setMessages([]);
  };

  return { messages, addUserMessage, addBotMessage, clearChat };
}
