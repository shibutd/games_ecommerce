import React, { useState, createContext } from 'react';
import PropTypes from "prop-types";

export const UserContext = createContext();

export const UserContextProvider = props => {
    const [isUserStaff, setIsUserStaff] = useState(false);

    return (
        <UserContext.Provider value={[isUserStaff, setIsUserStaff]}>
            {props.children}
        </UserContext.Provider>
    );
}

UserContextProvider.propTypes = {
  children: PropTypes.oneOfType([
    PropTypes.arrayOf(PropTypes.node),
    PropTypes.node
  ]).isRequired
}

export const DataContext = createContext();

export const DataContextProvider = props => {
    const [data, setData] = useState([]);

    return (
        <DataContext.Provider value={[data, setData]}>
            {props.children}
        </DataContext.Provider>
    );
}

DataContextProvider.propTypes = {
  children: PropTypes.oneOfType([
    PropTypes.arrayOf(PropTypes.node),
    PropTypes.node
  ]).isRequired
}
