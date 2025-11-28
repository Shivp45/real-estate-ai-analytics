import React, { useEffect, useState } from "react";
import { fetchMyHistory } from "../api/client";
import { LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid, Legend } from "recharts";
import jsPDF from "jspdf";
import autoTable from "jspdf-autotable";

const MyHistoryPage = () => {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchMyHistory()
      .then((res) => {
        if (res.success) setHistory(res.history);
      })
      .finally(() => setLoading(false));
  }, []);

  const exportPDF = (record) => {
    const pdf = new jsPDF();
    pdf.text(`Report - ${record.query}`, 14, 10);

    if (record.summary) {
      pdf.text("Summary:", 14, 20);
      pdf.text(record.summary, 14, 28);
    }

    if (record.full_response?.table) {
      autoTable(pdf, {
        startY: 45,
        head: [record.full_response.table.columns],
        body: record.full_response.table.rows,
      });
    }

    pdf.save(`Report_${record.id}.pdf`);
  };

  return (
    <div className="container py-4">
      <h3>My Chat History</h3>

      {loading && <div>Loading...</div>}

      {!loading && history.length === 0 && (
        <div className="text-muted mt-3">No history recorded.</div>
      )}

      {history.map((record) => (
        <div key={record.id} className="card mb-3 shadow-sm">
          <div className="card-body">

            <div className="d-flex justify-content-between">
              <strong>{record.query}</strong>
              <small className="text-muted">
                {new Date(record.created_at).toLocaleString()}
              </small>
            </div>

            <p className="mt-2">{record.summary}</p>

            {/* Render Table */}
            {record.full_response?.table && (
              <div className="mt-3">
                <strong>Data Table:</strong>
                <table className="table table-bordered mt-2">
                  <thead>
                    <tr>
                      {record.full_response.table.columns.map((col, i) => (
                        <th key={i}>{col}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {record.full_response.table.rows.map((row, r) => (
                      <tr key={r}>
                        {row.map((cell, c) => (
                          <td key={c}>{cell}</td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {/* Render Charts */}
            {record.full_response?.charts?.length > 0 && (
              <div className="mt-4">
                <strong>Charts</strong>
                {record.full_response.charts.map((chart, i) => (
                  <LineChart
                    key={i}
                    width={380}
                    height={250}
                    data={chart.data}
                    className="mt-3"
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
            )}

            <button
              className="btn btn-outline-primary mt-3"
              onClick={() => exportPDF(record)}
            >
              Download PDF
            </button>
          </div>
        </div>
      ))}
    </div>
  );
};

export default MyHistoryPage;
