import React from "react";
import ProductRow from "./ProductRow";

export default function StorageTransfer({
  transfers = [],
  categories,
  storages,
  onAddTransfer,
  onRemoveTransfer,
  onUpdateTransfer
}) {
  return (
    <div className="storage-transfer-section">
      <div className="section-header">
        <div className="header-left">
          <h3>Storage Transfers</h3>
          <p className="section-description">Move products between storage facilities. Select source storage (where product currently is) and destination storage (where to move it to).</p>
        </div>
        <div className="header-right">
          <button className="btn add-storage-btn" onClick={onAddTransfer}>
            + Add Storage
          </button>
        </div>
      </div>

      {/* Individual Transfer Boxes */}
      <div className="transfer-rows">
        {transfers.map((transfer, index) => (
          <div key={transfer.id} className="transfer-row">
            <div className="transfer-row-header">
              <div className="destination-storage-cell">
                <div className="destination-input-wrapper">
                  <select
                    className="input storage-input destination-storage-input"
                    value={transfer.destinationStorage}
                    onChange={(e) => onUpdateTransfer(index, "destinationStorage", e.target.value)}
                  >
                    <option value="">Select Destination Storage (Where to move TO)</option>
                    {storages.map((s) => (
                      <option key={s.id} value={s.id}>
                        {s.name}
                      </option>
                    ))}
                  </select>
                  <button className="btn remove-transfer-btn" onClick={() => onRemoveTransfer(index)}>×</button>
                </div>
              </div>
              <div className="transfer-header-actions">
                <button className="btn add-product-btn" onClick={() => onAddTransfer()}>
                  + Add Product
                </button>
              </div>
            </div>
            
            <div className="product-rows">
              <ProductRow
                pr={transfer}
                categories={categories}
                storages={storages}
                onChange={(field, value) => onUpdateTransfer(index, field, value)}
                onRemove={() => onRemoveTransfer(index)}
              />
            </div>
          </div>
        ))}
      </div>

      {/* Show message if no transfers */}
      {transfers.length === 0 && (
        <div className="no-transfers-message">
          <p>No storage transfers added. Click "+ Add Storage" to add transfers.</p>
        </div>
      )}
    </div>
  );
}
