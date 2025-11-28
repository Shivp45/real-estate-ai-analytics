import React, { useState, useContext } from "react";
import ChatLayout from "../components/ChatLayout.jsx";
import { analyzeQuery, uploadDataset } from "../api/client.js";
import { AuthContext } from "../context/AuthContext";
import { useChatHistory } from "../hooks/useChatHistory.js";

const ChatPage = () => {
  const { user, isAdmin } = useContext(AuthContext);

  // Persistent chat history tied to logged-in user
  const { messages, addUserMessage, addBotMessage, clearChat } =
    useChatHistory(user?.id);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSend = async (text) => {
    setError("");
    addUserMessage(text);
    setLoading(true);

    try {
      const res = await analyzeQuery(text);

      if (!res.success) {
        addBotMessage({
          type: "bot",
          error:
            res?.error?.message ||
            "Something went wrong processing your query.",
        });
      } else {
        // FIX: read correct structure from backend
        const summary = res?.data?.summary;
        const charts = res?.data?.charts;
        const table = res?.data?.table;

        addBotMessage({
          type: "bot",
          summary,
          charts,
          table,
        });
      }
    } catch (e) {
      addBotMessage({
        type: "bot",
        error: "⚠️ Unable to contact backend — ensure server is running.",
      });
      setError("Server unreachable.");
    } finally {
      setLoading(false);
    }
  };

  const handleDatasetUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!isAdmin) {
      setError("Only admins can upload datasets.");
      e.target.value = "";
      return;
    }

    setError("");
    setLoading(true);

    try {
      const res = await uploadDataset(file);

      if (!res.success) {
        setError(res?.error?.message || "Dataset upload failed.");
      } else {
        addBotMessage({
          type: "bot",
          summary: `📁 Dataset uploaded successfully. Rows: ${res.rows_loaded}`,
          charts: [],
          table: { columns: [], rows: [] },
        });
      }
    } catch {
      setError("Dataset upload error — check backend file format.");
    } finally {
      setLoading(false);
      e.target.value = "";
    }
  };

  const clearError = () => setError("");

  return (
    <div className="container py-2">
      {/* 🧹 Clear Chat Button */}
      <div className="text-end mb-2">
        <button
          className="btn btn-outline-danger btn-sm"
          onClick={() => {
            if (window.confirm("Are you sure you want to clear this conversation?")) {
              clearChat();
            }
          }}
        >
          🗑 Clear Chat
        </button>
      </div>

      {/* Chat UI */}
      <ChatLayout
        messages={messages}
        onSend={handleSend}
        loading={loading}
        error={error}
        clearError={clearError}
        onDatasetUpload={handleDatasetUpload}
      />
    </div>
  );
};

export default ChatPage;
