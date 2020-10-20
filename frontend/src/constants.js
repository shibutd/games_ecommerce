const localhost = 'http://localhost:8000';
const apiURL = '/api';

const endpoint = `${localhost}${apiURL}`;

export const orderSummaryURL = `${localhost}/order-summary/`;

export const orderListURL = `${apiURL}/orders/`;

export const IsUserStaffURL = `${endpoint}/is-user-staff/`;

export const orderLineUpdateURL = `${endpoint}/order-lines/`;

export const cartListURL = `${endpoint}/carts/`;

export const ordersPerDayURL = `${apiURL}/orders-per-day/`;

export const mostBoughtProductsURL = `${apiURL}/most-bought-products/`;

export const addToCartURL = `${endpoint}/add-to-cart/`;

export const removeSingleFromCartURL = `${endpoint}/remove-single-from-cart/`;

export const removeFromCartURL = `${endpoint}/remove-from-cart/`;
