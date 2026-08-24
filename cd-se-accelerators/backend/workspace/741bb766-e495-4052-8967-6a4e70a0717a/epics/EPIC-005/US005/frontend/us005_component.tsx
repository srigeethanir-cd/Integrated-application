import React, { useState } from 'react';

export const FeatureComponent = () => {
  const [data, setData] = useState(null);

  return (
    <div className="p-4 border rounded shadow-sm">
      <h2 className="text-xl font-bold">US005: Edit Task</h2>
      <p className="text-gray-600">Generated component for Edit Task</p>
      <button 
        className="mt-2 px-4 py-2 bg-blue-600 text-white rounded"
        onClick={() => setData("Executed")}
      >
        Action
      </button>
      {data && <div className="mt-2 text-green-600">Status: {data}</div>}
    </div>
  );
};

export default FeatureComponent;
