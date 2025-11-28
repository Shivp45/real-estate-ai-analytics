import React, { useEffect, useState } from "react";
import {
  fetchAdminUsers,
  changeUserRole,
  deleteUserAdmin,
  fetchUserHistoryAdmin,
  exportAllHistoryAdmin,
} from "../api/client";

import jsPDF from "jspdf";
import autoTable from "jspdf-autotable";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend,
} from "recharts";

const AdminPanelPage = () => {
  const [users, setUsers] = useState([]);
  const [selectedUserHistory, setSelectedUserHistory] = useState([]);
  const [selectedUser, setSelectedUser] = useState(null);
  const [adminPassword, setAdminPassword] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const loadUsers = () => {
    fetchAdminUsers()
      .then((res) => {
        if (res.success) setUsers(res.users);
        else setError("Failed to load users.");
      })
      .catch(() => setError("Failed to load users."));
  };

  useEffect(() => {
    loadUsers();
  }, []);

  const loadUserHistory = (userObj) => {
    setSelectedUser(userObj);
    setSelectedUserHistory([]);

    fetchUserHistoryAdmin(userObj.user.id).then((res) => {
      if (res.success) setSelectedUserHistory(res.history);
    });
  };

  const handleRoleChange = async (userObj, role) => {
    setMessage("");
    setError("");

    if (!adminPassword) return setError("Enter admin password.");

    try {
      const res = await changeUserRole(userObj.user.id, role, adminPassword);
      if (res.success) {
        setMessage("User role updated.");
        setAdminPassword("");
        loadUsers();
      } else setError(res.message);
    } catch {
      setError("Error while updating role.");
    }
  };

  const handleDeleteUser = async (userObj) => {
    if (!adminPassword) return setError("Admin password required.");
    if (!window.confirm(`Delete ${userObj.user.username}?`)) return;

    try {
      const res = await deleteUserAdmin(userObj.user.id, adminPassword);
      if (res.success) {
        setMessage("User deleted.");
        setSelectedUser(null);
        setSelectedUserHistory([]);
        loadUsers();
      } else setError(res.message);
    } catch {
      setError("Error while deleting.");
    }
  };

  /**
   * EXPORT — Single User History → PDF
   */
  const exportUserHistoryPDF = () => {
    if (!selectedUser || selectedUserHistory.length === 0) return;

    const pdf = new jsPDF();
    pdf.text(`${selectedUser.user.username} - Chat History`, 10, 10);

    selectedUserHistory.forEach((record, index) => {
      pdf.text(`Query: ${record.query}`, 10, 20 + index * 80);
      pdf.text(`Summary: ${record.summary}`, 10, 28 + index * 80);

      if (record.full_response?.table) {
        autoTable(pdf, {
          startY: 35 + index * 80,
          head: [record.full_response.table.columns],
          body: record.full_response.table.rows,
        });
      }
    });

    pdf.save(`${selectedUser.user.username}_History.pdf`);
  };

  /**
   * EXPORT — All system data → JSON (recommended for admin archive)
   */
  const exportAll = async () => {
    const res = await exportAllHistoryAdmin();
    if (!res.success) return alert("Export failed.");

    const json = JSON.stringify(res.export, null, 2);
    const blob = new Blob([json], { type: "application/json" });

    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `ALL_HISTORY_EXPORT_${Date.now()}.json`;
    a.click();
  };

  return (
    <div className="container py-4">
      <h3>Admin Panel</h3>
      <p className="text-muted">
        Manage users, roles, and view detailed stored history.
      </p>

      {/* Admin Password Box */}
      <div className="alert alert-light shadow-sm">
        <label className="form-label fw-bold">Admin Password (Required)</label>
        <input
          className="form-control"
          type="password"
          value={adminPassword}
          onChange={(e) => setAdminPassword(e.target.value)}
          placeholder="Enter your password before performing actions"
        />
      </div>

      {error && <div className="alert alert-danger">{error}</div>}
      {message && <div className="alert alert-success">{message}</div>}

      <div className="row">
        {/* ---------------- USERS LIST ---------------- */}
        <div className="col-md-6">
          <h5 className="mb-2">Registered Users</h5>

          {users.map((u) => (
            <div key={u.user.id} className="card mb-2 shadow-sm border-0">
              <div className="card-body">
                <strong>{u.user.username}</strong>
                <div className="small text-muted">
                  Role: {u.user.role} | History: {u.history_count}
                </div>

                <div className="mt-2 d-flex gap-1 flex-wrap">
                  <button
                    className="btn btn-sm btn-outline-primary"
                    onClick={() => loadUserHistory(u)}
                  >
                    View History
                  </button>
                  <button
                    className="btn btn-sm btn-outline-success"
                    onClick={() => handleRoleChange(u, "ADMIN")}
                  >
                    Promote
                  </button>
                  <button
                    className="btn btn-sm btn-outline-secondary"
                    onClick={() => handleRoleChange(u, "USER")}
                  >
                    Demote
                  </button>
                  <button
                    className="btn btn-sm btn-outline-danger"
                    onClick={() => handleDeleteUser(u)}
                  >
                    Delete
                  </button>
                </div>
              </div>
            </div>
          ))}

          {/* 🔥 Export Everything Button */}
          <button className="btn btn-dark mt-3 w-100" onClick={exportAll}>
            📁 Download Full System Export (JSON)
          </button>
        </div>

        {/* ---------------- USER HISTORY DISPLAY ---------------- */}
        <div className="col-md-6">
          <h5>User History</h5>

          {!selectedUser && <div className="text-muted">Select a user</div>}

          {selectedUser && (
            <>
              <div className="mt-2 fw-bold">
                {selectedUser.user.username}{" "}
                <span className="text-muted">
                  ({selectedUser.user.email || "no email"})
                </span>
              </div>

              <button
                className="btn btn-outline-warning btn-sm mt-2"
                onClick={exportUserHistoryPDF}
              >
                📄 Export PDF
              </button>

              <div style={{ maxHeight: "60vh", overflowY: "auto" }}>
                {selectedUserHistory.map((h) => (
                  <div key={h.id} className="card my-2 shadow-sm">
                    <div className="card-body">
                      <strong>{h.query}</strong>
                      <small className="d-block text-muted">
                        {new Date(h.created_at).toLocaleString()}
                      </small>
                      <p>{h.summary}</p>

                      {/* SHOW CHARTS */}
                      {h.full_response?.charts?.map((chart, i) => (
                        <LineChart
                          key={i}
                          width={350}
                          height={200}
                          data={chart.data}
                        >
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="year" />
                          <YAxis />
                          <Tooltip />
                          <Legend />
                          <Line type="monotone" dataKey="value" stroke="blue" />
                        </LineChart>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default AdminPanelPage;
