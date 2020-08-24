import React, { useState, useEffect, useContext, createContext } from 'react';
import PropTypes from "prop-types";
import { IsUserStaffURL } from './constants';

export const UserContext = createContext();

export const OrderContext = createContext();

export function useUserStaff() {
  return useContext(UserContext)
}

export const DashboardContextProvider = props => {
  const [isUserStaff, setIsUserStaff] = useState(false);
  const [data, setData] = useState([]);

  useEffect(() => {
    console.log('User useEffect called!')
    fetch(IsUserStaffURL)
      .then(response => response.json())
      .then(data => setIsUserStaff(data.is_staff))
      .catch(error => console.warn(error));
  }, [])

  return (
    <UserContext.Provider value={isUserStaff}>
      <OrderContext.Provider value={[data, setData]}>
        {props.children}
      </OrderContext.Provider>
    </UserContext.Provider>
  );
}

DashboardContextProvider.propTypes = {
  children: PropTypes.oneOfType([
    PropTypes.arrayOf(PropTypes.node),
    PropTypes.node
  ]).isRequired
}
