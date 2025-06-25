import React from "react";

export default function AssignmentResult({ assignedVehicles }) {
  if (!Array.isArray(assignedVehicles) || assignedVehicles.length === 0) return null;

  return (
    <div className="results-box">
      <h2>Assignment Results</h2>
      {assignedVehicles.map((veh, vi) => (
        <div className="vehicle-result" key={vi}>
          <h3>
            Vehicle: {veh.truckId} — Type: {veh.type} · Capacity: {veh.capacity}kg
          </h3>
          <p><strong>Current Load:</strong> {veh.currentLoad}kg</p>

          <div className="assigned-customers">
            <strong>Assigned Customers:</strong>
            <ul>
              {veh.assignedCustomers?.map((ac, ai) => (
                <li key={ai}>
                  {ac.customerName} ({ac.CustomerID}) – {ac.loadWeight}kg
                </li>
              ))}
            </ul>
          </div>

          <div className="route-list">
            <strong>Route:</strong>
            <ol>
              {veh.route?.map((step, si) => {
                const [type, idOrLat, latOrLng, lng] = step;

                if (type === "start") {
                  return (
                    <li key={si}>
                      🚚 Start at truck location ({idOrLat.toFixed(4)}, {latOrLng.toFixed(4)})
                    </li>
                  );
                }

                if (type === "storage") {
                    const name = veh.storages?.find(s => s.id === idOrLat)?.name
                  return (
                    <li key={si}>
                      🏭 Pick up at Storage {name} ({latOrLng.toFixed(4)}, {lng.toFixed(4)})
                    </li>
                  );
                }

                if (type === "customer") {
                    const name = veh.customers?.find(c => c.id === idOrLat)?.name;
                  return (
                    <li key={si}>
                      📦 Deliver to Customer {name} ({latOrLng.toFixed(4)}, {lng.toFixed(4)})
                    </li>
                  );
                }

                return <li key={si}>🔍 {JSON.stringify(step)}</li>;
              })}
            </ol>
          </div>
          <hr />
        </div>
      ))}
    </div>
  );
}
