import React, { useState, useEffect, useRef } from 'react';
import MapDisplay from './MapDisplay';
import './App.css';

function App() {
  const [dailyCustomerCount, setDailyCustomerCount] = useState("");

  const [customers, setCustomers] = useState([]);
  const [selectedCustomerIds, setSelectedCustomerIds] = useState([]);
  const [searchTerm, setSearchTerm] = useState("");

  const [storages, setStorages] = useState([]);
  const [selectedStorageId, setSelectedStorageId] = useState(null);
  const [searchStorageTerm, setSearchStorageTerm] = useState("");

  const [numTrucks, setNumTrucks] = useState("");
  const [productWeight, setProductWeight] = useState("");

  const [optimizationResult, setOptimizationResult] = useState(null);
  const suggestionRef = useRef(null);

  useEffect(() => {
    // fetch customers
    fetch("http://127.0.0.1:5000/customers")
      .then(res => res.json())
      .then(data => {
        setCustomers(data.customers.map(c => ({
          id:       c.CustomerID,
          name:     c.CustomerName,
          address:  c.CustomerAddress,
          location: [c.CustomerLat, c.CustomerLong],
        })));
      })
      .catch(console.error);

    // fetch storages
    fetch("http://127.0.0.1:5000/storages")
      .then(res => res.json())
      .then(data => {
        const list = data.storages.map(s => ({
          id:       s.StorageID,
          name:     s.StorageName,
          address:  s.StorageAddress,
          location: [s.StorageLat, s.StorageLong],
        }));
        setStorages(list);
        if (list.length) setSelectedStorageId(list[0].id);
      })
      .catch(console.error);

    // close dropdowns on outside click
    const onClickOutside = e => {
      if (suggestionRef.current && !suggestionRef.current.contains(e.target)) {
        setSearchTerm("");
        setSearchStorageTerm("");
      }
    };
    document.addEventListener('mousedown', onClickOutside);
    return () => document.removeEventListener('mousedown', onClickOutside);
  }, []);

  // toggle a stop
  const toggleCustomer = id =>
    setSelectedCustomerIds(ids =>
      ids.includes(id) ? ids.filter(x => x !== id) : [...ids, id]
    );

  // remove a stop tag
  const removeCustomer = id =>
    setSelectedCustomerIds(ids => ids.filter(x => x !== id));

  // remove storage tag
  const removeStorage = () =>
    setSelectedStorageId(null);

  // live suggestions
  const customerSuggestions = searchTerm.trim()
    ? customers.filter(c =>
        !selectedCustomerIds.includes(c.id) &&
        c.name.toLowerCase().includes(searchTerm.toLowerCase())
      ).slice(0,5)
    : [];

  const storageSuggestions = searchStorageTerm.trim()
    ? storages.filter(s =>
        s.name.toLowerCase().includes(searchStorageTerm.toLowerCase()) ||
        s.address.toLowerCase().includes(searchStorageTerm.toLowerCase())
      ).slice(0,5)
    : [];

  // submit to backend
  const handleSubmit = async () => {
    const depot = storages.find(s => s.id === selectedStorageId)?.location;
    if (!depot) return alert("Please select a storage first.");
    const stops = selectedCustomerIds.map(id =>
      customers.find(c => c.id === id).location
    );
    const payload = {
      locations:      [depot, ...stops],
      num_vehicles:   numTrucks,
      depot_index:    0,
      daily_customers: dailyCustomerCount,
      total_weight:   productWeight,
    };
    try {
      const res = await fetch("http://127.0.0.1:5000/optimize", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const json = await res.json();
      setOptimizationResult(json);
    } catch (e) {
      console.error(e);
      alert("Failed to optimize routes.");
    }
  };

  // map data
  const routeData    = optimizationResult?.optimized_route?.routes?.[0]?.route || [];
  const defaultCenter = storages.find(s => s.id === selectedStorageId)?.location || [0, 0];

  return (
    <div className="container">
      <header className="header">
        <div className="header-left">
          <h1 className="route-name">Delivery Optimizer</h1>
          <p className="route-desc">Your daily route optimization solution</p>
        </div>
        <div className="header-right">
          <button className="btn new-route">+ New Route</button>
        </div>
      </header>

      <div className="content">
        <aside className="sidebar" ref={suggestionRef}>

          {/* --- Storage Live Search --- */}
          <div className="storages-section">
            <h3>Storage</h3>

            <input
              type="text"
              className="search-input"
              placeholder="Search storage…"
              value={searchStorageTerm}
              onChange={e => setSearchStorageTerm(e.target.value)}
            />

            <div className="selected-tags">
              {selectedStorageId && (() => {
                const s = storages.find(x => x.id === selectedStorageId);
                return (
                  <span className="tag" key={s.id}>
                    {s.name}
                    <button onClick={removeStorage}>×</button>
                  </span>
                );
              })()}
            </div>

            {storageSuggestions.length > 0 && (
              <ul className="suggestions-list">
                {storageSuggestions.map(s => (
                  <li key={s.id} onClick={() => {
                    setSelectedStorageId(s.id);
                    setSearchStorageTerm("");
                  }}>
                    {s.name} — {s.address}
                  </li>
                ))}
              </ul>
            )}
          </div>

          {/* --- Customer Live Search --- */}
          <div className="stops-section">
            <h3>Stops</h3>

            <input
              type="text"
              className="search-input"
              placeholder="Type to search customers…"
              value={searchTerm}
              onChange={e => setSearchTerm(e.target.value)}
            />

            <div className="selected-tags">
              {selectedCustomerIds.map(id => {
                const c = customers.find(x => x.id === id);
                return (
                  <span className="tag" key={id}>
                    {c.name}
                    <button onClick={() => removeCustomer(id)}>×</button>
                  </span>
                );
              })}
            </div>

            {customerSuggestions.length > 0 && (
              <ul className="suggestions-list">
                {customerSuggestions.map(c => (
                  <li key={c.id} onClick={() => {
                    toggleCustomer(c.id);
                    setSearchTerm("");
                  }}>
                    {c.name} — {c.address}
                  </li>
                ))}
              </ul>
            )}
          </div>
        </aside>

        <main className="main-area">
          <div className="form-section">
            <div className="input-group">
              <label>Daily Customer Count:</label>
              <input
                type="number" min="0"
                value={dailyCustomerCount}
                onChange={e => setDailyCustomerCount(+e.target.value)}
                className="number-input"
              />
            </div>
            <div className="input-group">
              <label>Trucks Needed:</label>
              <input
                type="number" min="0"
                value={numTrucks}
                onChange={e => setNumTrucks(+e.target.value)}
                className="number-input"
              />
            </div>
            <div className="input-group">
              <label>Product Weight (kg):</label>
              <input
                type="number" min="0"
                value={productWeight}
                onChange={e => setProductWeight(+e.target.value)}
                className="number-input"
              />
            </div>
            <button onClick={handleSubmit} className="btn optimize-btn">
              Submit for Optimized Route
            </button>
          </div>

          <div className="map-container">
            <MapDisplay
              routeData={routeData}
              defaultCenter={defaultCenter}
              zoom={13}
            />
          </div>
        </main>
      </div>

      {optimizationResult && (
        <div className="result-container">
          <h2>Optimization Result</h2>
          <pre className="result-output">
            {JSON.stringify(optimizationResult, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}

export default App;
