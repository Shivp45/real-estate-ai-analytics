import React from "react";
import ResponseCard from "./ResponseCard.jsx";

const MessageList = ({ messages }) => {
  if (!messages.length) {
    return (
      <div className="text-muted text-center py-5">
        <p className="mb-2">Start by asking something like:</p>
        <code className="d-block">Analyze Wakad</code>
        <code className="d-block mt-1">Compare Ambegaon Budruk and Aundh demand trends</code>
        <code className="d-block mt-1">Show price growth for Akurdi over the last 3 years</code>
      </div>
    );
  }

  return (
    <div className="message-list">
      {messages.map((msg) => {
        if (msg.type === "user") {
          return (
            <div key={msg.id} className="d-flex justify-content-end mb-2">
              <div className="badge bg-primary text-wrap text-start user-bubble">
                {msg.text}
              </div>
            </div>
          );
        }
        if (msg.type === "bot") {
          return (
            <div key={msg.id} className="d-flex justify-content-start mb-2">
              <div className="bot-bubble flex-grow-1">
                {msg.error ? (
                  <div className="alert alert-warning mb-0">
                    <strong>Note:</strong> {msg.error}
                  </div>
                ) : (
                  <ResponseCard
                    summary={msg.summary}
                    charts={msg.charts}
                    table={msg.table}
                  />
                )}
              </div>
            </div>
          );
        }
        return null;
      })}
    </div>
  );
};

export default MessageList;
