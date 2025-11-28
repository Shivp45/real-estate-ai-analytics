import React from "react";
import MessageList from "./MessageList.jsx";
import MessageInput from "./MessageInput.jsx";
import ErrorAlert from "./ErrorAlert.jsx";
import LoadingSpinner from "./LoadingSpinner.jsx";

const ChatLayout = ({
  messages,
  onSend,
  loading,
  error,
  clearError,
  onDatasetUpload
}) => {
  return (
    <div className="container py-4 chat-container">
      <div className="row justify-content-center">
        <div className="col-lg-8">
          <div className="d-flex justify-content-between align-items-center mb-3">
            <div>
              <h3 className="mb-0">Real Estate Analytics Chatbot</h3>
              <small className="text-muted">
                Ask about locality trends, demand, and price growth.
              </small>
            </div>
            <div>
              <label className="btn btn-outline-secondary btn-sm mb-0">
                Upload Dataset
                <input
                  type="file"
                  accept=".xlsx,.xls"
                  hidden
                  onChange={onDatasetUpload}
                />
              </label>
            </div>
          </div>

          <ErrorAlert message={error} onClose={clearError} />

          <div className="card border-0 shadow-sm chat-card">
            <div className="card-body d-flex flex-column">
              <div className="flex-grow-1 overflow-auto mb-2">
                <MessageList messages={messages} />
              </div>
              {loading && <LoadingSpinner />}
              <MessageInput onSend={onSend} disabled={loading} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatLayout;
