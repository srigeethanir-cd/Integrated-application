typescript
// Product.ts
export interface Product {
  id: number;
  name: string;
  sku: string;
}

// productForm.ts
import React, { useState } from 'react';
import axios from 'axios';

const ProductForm = () => {
  const [name, setName] = useState('');
  const [sku, setSku] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    try {
      if (!name) {
        setError('Product name is mandatory.');
        return;
      }
      const response = await axios.post('/api/products', { name, sku });
      if (response.status === 201) {
        setSuccess(true);
        setError('');
        setName('');
        setSku('');
      } else {
        setError('Failed to create product.');
      }
    } catch (error: any) {
      if (error.response.status === 400) {
        setError(error.response.data.detail);
      } else {
        setError('Failed to create product.');
      }
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <label>
        Product Name:
        <input type="text" value={name} onChange={(event) => setName(event.target.value)} />
      </label>
      <br />
      <label>
        SKU:
        <input type="text" value={sku} onChange={(event) => setSku(event.target.value)} />
      </label>
      <br />
      <button type="submit">Create Product</button>
      {error && <p style={{ color: 'red' }}>{error}</p>}
      {success && <p style={{ color: 'green' }}>Product created successfully.</p>}
    </form>
  );
};

export default ProductForm;