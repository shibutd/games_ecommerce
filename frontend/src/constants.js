const localhost = 'http://127.0.0.1:8000';
const apiURL = '/api';

const endpoint = `${localhost}${apiURL}`;

export const orderSummaryURL = `${localhost}/order-summary/`;

export const orderListURL = `${endpoint}/orders/`;

export const IsUserStaffURL = `${endpoint}/is-user-staff/`;

export const orderLineUpdateURL = `${endpoint}/order-lines/`;

export const cartListURL = `${endpoint}/carts/`;

export const addToCartURL = `${endpoint}/add-to-cart/`;

export const removeSingleFromCartURL = `${endpoint}/remove-single-from-cart/`;

export const removeFromCartURL = `${endpoint}/remove-from-cart/`;
