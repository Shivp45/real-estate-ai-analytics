import React from "react";

const ErrorAlert = ({ message, onClose }) => {
  if (!message) return null;
  return (
    <div className="alert alert-danger d-flex justify-content-between align-items-center mt-2" role="alert">
      <span>{message}</span>
      {onClose && (
        <button type="button" className="btn-close" onClick={onClose} aria-label="Close"></button>
      )}
    </div>
  );
};

export default ErrorAlert;
