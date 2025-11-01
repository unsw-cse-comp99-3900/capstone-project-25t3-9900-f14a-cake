import React from 'react';
import { Link } from 'react-router-dom';

const ValidatePage = () => {
  return (
    <div>
      <h1>Validate Invoice</h1>
      <p>This is where the invoice validation form will go.</p>
      <Link to="/">Back to Welcome</Link>
    </div>
  );
};

export default ValidatePage;