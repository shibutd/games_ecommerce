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

  const updateOrderLine = async (e, orderlineId) => {
    const url = `${orderLineUpdateURL}${orderlineId}`;
    const csrftoken = Cookies.get('csrftoken');
    try {
      const response = await fetch(
        url, {
          method: 'PATCH',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken
          },
          body: JSON.stringify({"status": e.target.value})
        }
      )

      if (!response.ok) {
        throw new Error(
          `${response.status} ${response.statusText}`
        );
      }

      return await response;

    } catch (e) {
      console.log(e);
    }
  }

  const updateOrder = async (orderId) => {
    const url = `${orderListURL}${orderId}`;
    try {
      const response = await fetch(url)

      if (!response.ok) {
        throw new Error(
          `${response.status} ${response.statusText}`
        );
      }

      const orderData = await response.json();
      const orders = data.results.map(
        order => order.id == orderId ? orderData : order
      );
      setData({...data, results: orders});

    } catch (e) {
      console.log(e);
    }
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
              .then(resp => {
                if (resp.ok) {
                  updateOrder(props.order_id);
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
