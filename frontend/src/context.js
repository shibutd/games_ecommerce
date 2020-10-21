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
    const abortController = new AbortController();

    const fetchData = async () => {
      try {
        const response = await fetch(
          IsUserStaffURL,
          { signal: abortController.signal }
        )

        if (!response.ok) {
          throw new Error(
            `${response.status} ${response.statusText}`
          );
        }

        const data = await response.json();
        setIsUserStaff(data.is_staff);

      } catch (e) {
        console.log(e);
      }
    };

    fetchData();

    return () => {
      abortController.abort();
    }
  }, []);

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
