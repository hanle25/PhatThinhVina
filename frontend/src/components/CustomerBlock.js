import React from "react";
import ProductRow from "./ProductRow";

export default function CustomerBlock({
  block,
  blockIdx,
  searchTerm,
  suggestions,
  customers,
  categories,
  storages,
  onCustomerSearch,
  onCustomerSelect,
  onRemoveBlock,
  onAddProductRow,
  onRemoveProductRow,
  onUpdateProductField,
  suggestionRef
}) {
  return (
    <div className="customer-block">
      <div className="customer-row-header">
        <div className="customer-search-cell" ref={suggestionRef}>
          <div className="suggestion-wrapper">
            <input
              className="input customer-input"
              placeholder="Type to search customers…"
              value={searchTerm !== undefined ? searchTerm : block.customerName}
              onChange={(e) => onCustomerSearch(e.target.value)}
            />
            {suggestions?.length > 0 && (
              <ul className="suggestions-list">
                {suggestions.map((c) => (
                  <li key={c.id} onClick={() => onCustomerSelect(c)}>
                    {c.name} — {c.address}
                  </li>
                ))}
              </ul>
            )}
          </div>
          <button className="btn remove-customer-btn" onClick={onRemoveBlock}>×</button>
        </div>

        <div className="customer-header-actions">
          <button className="btn add-product-btn" onClick={onAddProductRow}>
            + Add Product
          </button>
        </div>
      </div>

      <div className="product-rows">
        {block.productRows.map((pr, prodIdx) => (
          <ProductRow
            key={pr.id}
            pr={pr}
            categories={categories}
            storages={storages}
            onChange={(field, value) => onUpdateProductField(prodIdx, field, value)}
            onRemove={() => onRemoveProductRow(prodIdx)}
          />
        ))}
      </div>
    </div>
  );
}
