import React from 'react';

export interface HeaderProps {
  // Add props here
}

export const Header: React.FC<HeaderProps> = () => {
  return (
    <div>
      <h3>Header Component</h3>
    </div>
  );
};

export default Header;
