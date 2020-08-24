import React, { useContext } from 'react';
import PropTypes from "prop-types";
import { makeStyles } from '@material-ui/core/styles';
import MenuItem from '@material-ui/core/MenuItem';
import FormControl from '@material-ui/core/FormControl';
import Select from '@material-ui/core/Select';
import Cookies from 'js-cookie';
import { orderListURL, orderLineUpdateURL } from './constants';
import { OrderContext } from "./context";

const useStyles = makeStyles((theme) => ({
  formControl: {
    margin: theme.spacing(1),
  },
  selectEmpty: {
    marginTop: theme.spacing(2),
  },
}));

export default function OrderLineStatusSelect(props) {
  const classes = useStyles();
  const [data, setData] = useContext(OrderContext);

  const updateOrderLine = (e, id) => {
    const URL = `${orderLineUpdateURL}${id}`;
    const csrftoken = Cookies.get('csrftoken');
    const response = fetch(URL, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrftoken
      },
      body: JSON.stringify({"status": e.target.value})
    });

    return response;
  }

  return (
    <div>
      <FormControl margin={'none'} className={classes.formControl}>
        <Select
          id={props.id}
          order_id={props.order_id}
          value={props.orderLineStatus}
          disabled={props.orderLineStatus === 20}
          onChange={(e) => {
            updateOrderLine(e, props.id)
            .then(response => {
              if (response.status === 200) {
                fetch(`${orderListURL}${props.order_id}`)
                  .then(response => response.json())
                  .then(orderData => {
                    const orders = data.results.map(
                      order => order.id == props.order_id ? orderData : order
                    );
                    setData({...data, results: orders});
                  })
              }
            })
          }}
          autoWidth
          style={{ fontSize: 14 }}
        >
          <MenuItem style={{ fontSize: 14 }} value={10}>Processing</MenuItem>
          <MenuItem style={{ fontSize: 14 }} value={20}>Sent</MenuItem>
        </Select>
      </FormControl>
    </div>
  );
}

OrderLineStatusSelect.propTypes = {
  id: PropTypes.string,
  order_id: PropTypes.string,
  orderLineStatus: PropTypes.number
}
