import React from "react";

export default function ProductRow({
  pr,
  categories,
  storages,
  onChange,
  onRemove
}) {
  return (
    <div className="product-row">
      {/* Category dropdown */}
      <div className="cell">
        <select
          className="input category-input"
          value={pr.category}
          onChange={(e) => onChange("category", e.target.value)}
        >
          <option value="">Select Category</option>
          {categories.map((c) => (
            <option key={c.id} value={c.id}>
              {c.name}
            </option>
          ))}
        </select>
      </div>

      {/* Quantity input */}
      <div className="cell">
        <input
          className="input quantity-input"
          type="text"
          placeholder="Quantity"
          value={pr.quantity}
          onChange={(e) => onChange("quantity", e.target.value)}
        />
      </div>

      {/* Weight input */}
      <div className="cell">
        <input
          className="input weight-input"
          type="text"
          placeholder="Weight"
          value={pr.weight}
          onChange={(e) => onChange("weight", e.target.value)}
        />
      </div>

      {/* Storage dropdown */}
      <div className="cell">
        <select
          className="input storage-input"
          value={pr.StorageID}
          onChange={(e) => onChange("StorageID", e.target.value)}
        >
          <option value="">Select Storage</option>
          {storages.map((s) => (
            <option key={s.id} value={s.id}>
              {s.name}
            </option>
          ))}
        </select>
      </div>

      {/* Remove product row */}
      <div className="remove-product-cell">
        <button className="btn remove-product-btn" onClick={onRemove}></button>
      </div>
    </div>
  );
}
