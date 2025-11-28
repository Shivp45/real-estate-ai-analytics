import React, { useState } from "react";

const MessageInput = ({ onSend, disabled }) => {
  const [text, setText] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    const trimmed = text.trim();
    if (!trimmed) return;
    onSend(trimmed);
    setText("");
  };

  return (
    <form onSubmit={handleSubmit} className="mt-3">
      <div className="input-group">
        <input
          type="text"
          className="form-control"
          placeholder="Ask about localities, price trends, demand, growth..."
          value={text}
          onChange={(e) => setText(e.target.value)}
          disabled={disabled}
        />
        <button className="btn btn-primary" type="submit" disabled={disabled}>
          Send
        </button>
      </div>
      <div className="form-text">
        Example: <code>Compare Ambegaon Budruk and Aundh demand trends</code>
      </div>
    </form>
  );
};

export default MessageInput;
