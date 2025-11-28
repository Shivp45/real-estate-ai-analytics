import React from "react";

const DataTable = ({ table }) => {
  if (!table || !table.rows || table.rows.length === 0) {
    return null;
  }

  return (
    <div className="mt-3">
      <h6 className="fw-semibold">Data Table</h6>
      <div className="table-responsive" style={{ maxHeight: "280px" }}>
        <table className="table table-sm table-striped align-middle">
          <thead className="table-light sticky-top">
            <tr>
              {table.columns.map((col) => (
                <th key={col}>{col}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {table.rows.map((row, idx) => (
              <tr key={idx}>
                {table.columns.map((col) => (
                  <td key={col}>{row[col] !== null && row[col] !== undefined ? row[col] : "-"}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default DataTable;
