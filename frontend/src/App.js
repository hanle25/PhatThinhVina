// src/DeliveryOptimizerSinglePage.js
import React, { useState, useEffect } from 'react';
import MapDisplay from './MapDisplay';
import './App.css';

function DeliveryOptimizerSinglePage() {
  // State for daily customer count.
  const [dailyCustomerCount, setDailyCustomerCount] = useState(0);

  // Customer-related state.
  const [customers, setCustomers] = useState([]);
  const [selectedCustomerIds, setSelectedCustomerIds] = useState([]);
  const [searchTerm, setSearchTerm] = useState("");

  // Truck & product details.
  const [numTrucks, setNumTrucks] = useState(0);
  const [productWeight, setProductWeight] = useState(0);

  // Storage options and selected storage.
  const [storages, setStorages] = useState([]);
  const [selectedStorageId, setSelectedStorageId] = useState(null);

  // Optimization result.
  const [optimizationResult, setOptimizationResult] = useState(null);

  // Fetch customers from backend database.
  useEffect(() => {
    fetch("http://127.0.0.1:5000/customers")
      .then(response => response.json())
      .then(data => {
        // Assuming your API returns { "customers": [ ... ] }
        setCustomers(data.customers);
      })
      .catch(err => console.error("Error fetching customers:", err));
  }, []);

  // Fetch storages from backend database.
  useEffect(() => {
    fetch("http://127.0.0.1:5000/storages")
      .then(response => response.json())
      .then(data => {
        // Assuming your API returns { "storages": [ ... ] }
        setStorages(data.storages);
        // Set default storage if available.
        if(data.storages && data.storages.length > 0) {
          setSelectedStorageId(data.storages[0].id);
        }
      })
      .catch(err => console.error("Error fetching storages:", err));
  }, []);

  // Toggle customer selection.
  const handleCustomerToggle = (customerId) => {
    setSelectedCustomerIds((prevSelected) =>
      prevSelected.includes(customerId)
        ? prevSelected.filter((id) => id !== customerId)
        : [...prevSelected, customerId]
    );
  };

  // Filter customers based on search.
  const filteredCustomers = customers.filter(
    (customer) =>
      customer.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      customer.address.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Handler to submit the form.
  const handleSubmit = async () => {
    // Filter selected customers from database-sourced list.
    const selectedCustomers = customers.filter((c) =>
      selectedCustomerIds.includes(c.id)
    );
    // Map each customer to its location (assuming each customer has a 'location' property 
    // that is an array like [lat, lng])
    const customerLocations = selectedCustomers.map((c) => c.location);
    const selectedStorage = storages.find(s => s.id === selectedStorageId);

    const payload = {
      locations: customerLocations,                   // Customer coordinates.
      num_vehicles: numTrucks,                         // Number of trucks.
      depot: selectedStorage ? selectedStorage.location : null,  // Depot (storage) coordinates.
      storage_address: selectedStorage ? selectedStorage.address : '',
      daily_customers: dailyCustomerCount,
      total_weight: productWeight,
    };

    try {
      const response = await fetch("http://127.0.0.1:5000/optimize", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const jsonData = await response.json();
      setOptimizationResult(jsonData);
    } catch (error) {
      console.error("Error optimizing routes:", error);
    }
  };

  // Determine the routeData for the MapDisplay.
  const routeData = optimizationResult &&
    optimizationResult.routes &&
    optimizationResult.routes.length > 0 &&
    optimizationResult.routes[0].route
      ? optimizationResult.routes[0].route
      : [];

  // Determine default map center from selected storage.
  const defaultCenter = storages.find(s => s.id === selectedStorageId)?.location || [0, 0];

  return (
    <div className="container">
      <h1 className="title">Delivery Optimizer</h1>
      
      {/* Form Inputs */}
      <div className="input-group">
        <label>
          <strong>Daily Customer Count:</strong>
          <input
            type="number"
            min="0"
            value={dailyCustomerCount}
            onChange={(e) => setDailyCustomerCount(Number(e.target.value))}
            className="number-input"
          />
        </label>
      </div>
      
      <div className="input-group">
        <h2>Select Storage</h2>
        <select
          value={selectedStorageId || ''}
          onChange={(e) => setSelectedStorageId(Number(e.target.value))}
          className="select-input"
        >
          {storages.map(storage => (
            <option key={storage.id} value={storage.id}>
              {storage.name} - {storage.address}
            </option>
          ))}
        </select>
      </div>
      
      <div className="input-group">
        <h2>Select Customers for Delivery</h2>
        <input
          type="text"
          placeholder="Search customers..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="text-input"
        />
        <div className="customer-list">
          {filteredCustomers.map((customer) => (
            <div
              key={customer.id}
              onClick={() => handleCustomerToggle(customer.id)}
              className={`customer-item ${selectedCustomerIds.includes(customer.id) ? 'selected' : ''}`}
            >
              <strong>{customer.name}</strong>
              <br />
              <small>{customer.address}</small>
            </div>
          ))}
          {filteredCustomers.length === 0 && (
            <p>No customers match your search criteria.</p>
          )}
        </div>
      </div>
      
      <div className="input-group">
        <h2>Truck & Product Details</h2>
        <div className="detail-group">
          <label>
            Number of Trucks Needed:
            <input
              type="number"
              min="0"
              value={numTrucks}
              onChange={(e) => setNumTrucks(Number(e.target.value))}
              className="number-input"
            />
          </label>
        </div>
        <div className="detail-group">
          <label>
            Product Weight (kg):
            <input
              type="number"
              min="0"
              value={productWeight}
              onChange={(e) => setProductWeight(Number(e.target.value))}
              className="number-input"
            />
          </label>
        </div>
      </div>
      
      <button onClick={handleSubmit} className="submit-button">
        Submit for Optimized Route
      </button>
      
      {/* Fixed Map Container at Bottom */}
      <div className="fixed-map-container">
        <MapDisplay routeData={routeData} defaultCenter={defaultCenter} />
      </div>
      
      {/* Optionally display the optimization result JSON above the map if desired */}
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

export default DeliveryOptimizerSinglePage;
