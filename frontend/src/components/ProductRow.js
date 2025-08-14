import React, { useState, useEffect, useRef } from "react";

export default function ProductRow({
  pr,
  categories,
  storages,
  onChange,
  onRemove
}) {
  const [showStorageDropdown, setShowStorageDropdown] = useState(false);
  const dropdownRef = useRef(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setShowStorageDropdown(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  // Parse current storage selection (handle both single and multiple)
  const getSelectedStorages = () => {
    if (!pr.StorageID) return [];
    return pr.StorageID.split('/').filter(id => id.trim());
  };

  const selectedStorages = getSelectedStorages();

  const handleStorageToggle = (storageId) => {
    let newStorageIds;
    
    if (selectedStorages.includes(storageId)) {
      // Remove storage
      newStorageIds = selectedStorages.filter(id => id !== storageId);
    } else {
      // Add storage
      newStorageIds = [...selectedStorages, storageId];
    }
    
    // Convert back to string format for backend
    const storageString = newStorageIds.length > 0 ? newStorageIds.join('/') : '';
    onChange("StorageID", storageString);
  };

  const getDisplayText = () => {
    if (selectedStorages.length === 0) return "Select Storage";
    if (selectedStorages.length === 1) {
      const storage = storages.find(s => s.id === selectedStorages[0]);
      return storage ? storage.name : selectedStorages[0];
    }
    // Show storage names separated by "/"
    const storageNames = selectedStorages.map(storageId => {
      const storage = storages.find(s => s.id === storageId);
      return storage ? storage.name : storageId;
    });
    return storageNames.join(' / ');
  };

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

      {/* Multi-select Storage dropdown */}
      <div className="cell">
        <div className="multi-select-container" ref={dropdownRef}>
          <div 
            className="input storage-input multi-select-trigger"
            onClick={() => setShowStorageDropdown(!showStorageDropdown)}
          >
            <span>{getDisplayText()}</span>
            <span className="dropdown-arrow">▼</span>
          </div>
          
          {showStorageDropdown && (
            <div className="multi-select-dropdown">
              {storages.map((storage) => (
                <div 
                  key={storage.id} 
                  className="storage-option"
                  onClick={() => handleStorageToggle(storage.id)}
                >
                  <input
                    type="checkbox"
                    checked={selectedStorages.includes(storage.id)}
                    onChange={() => {}} // Controlled by onClick
                    className="storage-checkbox"
                  />
                  <span className="storage-name">{storage.name}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Remove product row */}
      <div className="remove-product-cell">
        <button className="btn remove-product-btn" onClick={onRemove}>×</button>
      </div>
    </div>
  );
}
