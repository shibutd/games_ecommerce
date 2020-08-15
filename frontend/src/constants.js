const localhost = 'http://127.0.0.1:8000';
const apiURL = '/api';

const endpoint = `${localhost}${apiURL}`;

export const orderListURL = `${endpoint}/orders/`;

export const IsUserStaffURL = `${endpoint}/is-user-staff/`;

export const orderLineUpdateURL = `${endpoint}/order-lines/`;
