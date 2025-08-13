import React, { useState, useEffect, useRef } from "react";
import "./App.css";
import CustomerBlock from "./components/CustomerBlock";
import StorageTransfer from "./components/StorageTransfer";
import AssignmentResult from "./components/AssignmentResult";
import ErrorBoundary from "./components/ErrorBoundary";

const API_FETCH_CUSTOMERS = process.env.REACT_APP_API_URL_CUSTOMERS;
const API_FETCH_STORAGES = process.env.REACT_APP_API_URL_STORAGES;
const API_FETCH_CATALOGS = process.env.REACT_APP_API_URL_CATALOGS;
const API_ASSIGN_TRUCKS = process.env.REACT_APP_API_ASSIGN_TRUCKS;
// const API_NAME_MAPS = process.env.REACT_APP_API_NAME_MAPS;

function App() {
  const [customers, setCustomers] = useState([]);
  const [storages, setStorages] = useState([]);
  const [categories, setCategories] = useState([]);
  const [searchTerms, setSearchTerms] = useState([]);
  const [customerSuggestions, setCustomerSuggestions] = useState([]);
  const [customerBlocks, setCustomerBlocks] = useState([]);
  const [storageTransfers, setStorageTransfers] = useState([]);
  const [assignedVehicles, setAssignedVehicles] = useState([]);
  // const [customerNameMap, setCustomerNameMap] = useState({});
  // const [storageNameMap, setStorageNameMap] = useState({});
  const suggestionRefs = useRef([]);

  useEffect(() => {
    fetch(API_FETCH_CUSTOMERS)
      .then(res => res.json())
      .then(data => {
        setCustomers(data.customers.map(c => ({
          id: c.CustomerID,
          name: c.CustomerName,
          address: c.CustomerAddress,
          location: [c.CustomerLat, c.CustomerLong]
        })));
      });

    fetch(API_FETCH_STORAGES)
      .then(res => res.json())
      .then(data => {
        setStorages(data.storages.map(s => ({
          id: s.StorageID,
          name: s.StorageName,
          address: s.StorageAddress,
          location: [s.StorageLat, s.StorageLong]
        })));
      });

    fetch(API_FETCH_CATALOGS)
      .then(res => res.json())
      .then(data => {
        setCategories(data.catalogs.map(c => ({
          id: c.CatalogID,
          name: c.CatalogName
        })));
      });
  }, []);

  useEffect(() => {
    if (customerBlocks.length === 0) addCustomerBlock();
  }, [customerBlocks.length]);

  // useEffect(() => {
  //   fetch(API_NAME_MAPS)
  //     .then((res) => res.json())
  //     .then((data) => {
  //       setCustomerNameMap(data.customerNameMap || {});
  //       setStorageNameMap(data.storageNameMap || {});
  //     })
  //     .catch((err) => console.error("Failed to fetch name maps:", err));
  // }, []);

  const addCustomerBlock = () => {
    const newBlock = {
      id: Date.now() + Math.random(),
      CustomerID: "",
      customerName: "",
      productRows: [{
        id: Date.now() + Math.random() + 1,
        category: "",
        quantity: "",
        weight: "",
        StorageID: "",
        storageName: ""
      }]
    };
    setCustomerBlocks(prev => [...prev, newBlock]);
    setSearchTerms(prev => [...prev, { customer: "" }]);
    setCustomerSuggestions(prev => [...prev, []]);
  };

  const removeCustomerBlock = idx => {
    setCustomerBlocks(prev => prev.filter((_, i) => i !== idx));
    setSearchTerms(prev => prev.filter((_, i) => i !== idx));
    setCustomerSuggestions(prev => prev.filter((_, i) => i !== idx));
  };

  const updateProductField = (blockIdx, prodIdx, field, value) => {
    setCustomerBlocks(prev => prev.map((block, i) => {
      if (i !== blockIdx) return block;
      return {
        ...block,
        productRows: block.productRows.map((pr, j) =>
          j === prodIdx ? { ...pr, [field]: value } : pr
        )
      };
    }));
  };

  const handleSubmit = async () => {
    for (let i = 0; i < customerBlocks.length; i++) {
      const blk = customerBlocks[i];
      if (!blk.CustomerID && blk.customerName.trim() !== "") {
        const match = customers.find(c => c.name.toLowerCase() === blk.customerName.trim().toLowerCase());
        if (match) blk.CustomerID = match.id;
      }
    }

    for (let i = 0; i < customerBlocks.length; i++) {
      const blk = customerBlocks[i];
      blk.productRows.forEach(pr => {
        if (!pr.StorageID && pr.storageName?.trim()) {
          const match = storages.find(s => s.name.toLowerCase() === pr.storageName.trim().toLowerCase());
          if (match) pr.StorageID = match.id;
        }
      });
    }

    const orders = [];
    for (const blk of customerBlocks) {
      if (!blk.CustomerID) return alert("Please select a customer.");
      for (const pr of blk.productRows) {
        if (!pr.category || !pr.weight || isNaN(parseFloat(pr.weight)) || !pr.StorageID) {
          return alert("Invalid product details detected.");
        }
        const cataName = categories.find(c => c.id === pr.category)?.name || "";
        orders.push({
          CustomerID: blk.CustomerID,
          cataName,
          weight: parseFloat(pr.weight),
          quantity: parseFloat(pr.quantity) || 1,
          StorageID: pr.StorageID,
          offRoute: false
        });
      }
    }

    // Add storage transfers to orders (optional)
    for (const transfer of storageTransfers) {
      if (transfer.destinationStorage && transfer.category && transfer.weight && transfer.StorageID) {
        const cataName = categories.find(c => c.id === transfer.category)?.name || "";
        orders.push({
          CustomerID: "TRANSFER", // Special identifier for transfers
          cataName,
          weight: parseFloat(transfer.weight),
          quantity: parseFloat(transfer.quantity) || 1,
          StorageID: transfer.StorageID, // Source storage (where product currently is)
          toStorage: transfer.destinationStorage, // Destination storage
          offRoute: false
        });
      }
    }

    try {
      const response = await fetch(API_ASSIGN_TRUCKS, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ orders })
      });
      if (!response.ok) throw new Error("Failed to assign trucks");
      const data = await response.json();
      console.log("🚚 Backend response:", data);  // 👈 This shows what you're getting from the server
      setAssignedVehicles(data.assigned_vehicles || []);

    } catch (err) {
      console.error(err);
      alert("Submission failed. See console.");
    }
  };

  const handleCustomerSearch = (blockIdx, value) => {
    setSearchTerms(prev => prev.map((t, i) => i === blockIdx ? { ...t, customer: value } : t));
    const suggestions = value.trim()
      ? customers.filter(c =>
          c.name.toLowerCase().includes(value.toLowerCase()) &&
          !customerBlocks.some((blk, i) => i !== blockIdx && blk.CustomerID === c.id)
        ).slice(0, 5)
      : [];
    setCustomerSuggestions(prev => prev.map((arr, i) => i === blockIdx ? suggestions : arr));
    setCustomerBlocks(prev => prev.map((blk, i) => i === blockIdx
      ? { ...blk, customerName: value, CustomerID: "" }
      : blk));
  };

  const handleCustomerSelect = (blockIdx, customer) => {
    setCustomerBlocks(prev => prev.map((blk, i) => i === blockIdx
      ? { ...blk, CustomerID: customer.id, customerName: customer.name }
      : blk));
    setCustomerSuggestions(prev => prev.map((arr, i) => (i === blockIdx ? [] : arr)));
    setSearchTerms(prev => prev.map((term, i) => (i === blockIdx ? { ...term, customer: undefined } : term)));
  };

  const addProductRow = (blockIdx) => {
    setCustomerBlocks(prev => prev.map((blk, i) => {
      if (i !== blockIdx) return blk;
      return {
        ...blk,
        productRows: [...blk.productRows, {
          id: Date.now() + Math.random(),
          category: "",
          quantity: "",
          weight: "",
          StorageID: "",
          storageName: ""
        }]
      };
    }));
  };

  const removeProductRow = (blockIdx, prodIdx) => {
    setCustomerBlocks(prev => prev.map((blk, i) => {
      if (i !== blockIdx) return blk;
      const newRows = blk.productRows.filter((_, j) => j !== prodIdx);
      return {
        ...blk,
        productRows: newRows.length > 0 ? newRows : [
          {
            id: Date.now() + Math.random(),
            category: "",
            quantity: "",
            weight: "",
            StorageID: "",
            storageName: ""
          }
        ]
      };
    }));
  };

  // Storage Transfer Management
  const addStorageTransfer = () => {
    const newTransfer = {
      id: Date.now() + Math.random(),
      destinationStorage: "",
      category: "",
      quantity: "",
      weight: "",
      StorageID: "",
      storageName: ""
    };
    setStorageTransfers(prev => [...prev, newTransfer]);
  };

  const removeStorageTransfer = (transferIdx) => {
    setStorageTransfers(prev => prev.filter((_, i) => i !== transferIdx));
  };

  const updateStorageTransfer = (transferIdx, field, value) => {
    setStorageTransfers(prev => prev.map((transfer, i) =>
      i === transferIdx ? { ...transfer, [field]: value } : transfer
    ));
  };

  return (
    <div className="container">

      <div className="content">
        <main className="main-area">
          {/* Assign Truck Section Container */}
          <div className="assign-truck-section">
            <div className="section-header">
              <div className="header-left">
                <h3>Assign Truck</h3>
              </div>
              <div className="header-right">
                <button className="btn add-customer-btn" onClick={addCustomerBlock}>
                  + Add Customer
                </button>
              </div>
            </div>

            <div className="customer-blocks">
              {customerBlocks.map((block, idx) => (
                <CustomerBlock
                  key={block.id}
                  block={block}
                  blockIdx={idx}
                  searchTerm={searchTerms[idx]?.customer}
                  suggestions={customerSuggestions[idx]}
                  customers={customers}
                  categories={categories}
                  storages={storages}
                  onCustomerSearch={(val) => handleCustomerSearch(idx, val)}
                  onCustomerSelect={(customer) => handleCustomerSelect(idx, customer)}
                  onRemoveBlock={() => removeCustomerBlock(idx)}
                  onAddProductRow={() => addProductRow(idx)}
                  onRemoveProductRow={(prodIdx) => removeProductRow(idx, prodIdx)}
                  onUpdateProductField={(prodIdx, field, value) =>
                    updateProductField(idx, prodIdx, field, value)}
                  suggestionRef={(el) => (suggestionRefs.current[idx] = el)}
                />
              ))}
            </div>
          </div>

          <ErrorBoundary>
            <StorageTransfer
              transfers={storageTransfers}
              categories={categories}
              storages={storages}
              onAddTransfer={addStorageTransfer}
              onRemoveTransfer={removeStorageTransfer}
              onUpdateTransfer={updateStorageTransfer}
            />
          </ErrorBoundary>

          <div className="submit-btn-row">
            <button className="btn submit-btn" onClick={handleSubmit}>Submit</button>
          </div>

          <AssignmentResult 
            assignedVehicles={assignedVehicles}
          />
        </main>
      </div>
    </div>
  );
}

export default App;
