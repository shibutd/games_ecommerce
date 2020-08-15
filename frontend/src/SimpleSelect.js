import React, { useContext } from 'react';
import PropTypes from "prop-types";
import { makeStyles } from '@material-ui/core/styles';
import InputLabel from '@material-ui/core/InputLabel';
import MenuItem from '@material-ui/core/MenuItem';
import FormControl from '@material-ui/core/FormControl';
import Select from '@material-ui/core/Select';
import Cookies from 'js-cookie';
import { orderListURL, orderLineUpdateURL } from './constants';
import { DataContext } from "./context";

const useStyles = makeStyles((theme) => ({
  formControl: {
    margin: theme.spacing(1),
  },
  selectEmpty: {
    marginTop: theme.spacing(2),
  },
}));

export function OrderStatusSelect(props) {
  const classes = useStyles();

  return (
    <div>
      <FormControl className={classes.formControl}>
        <InputLabel id="demo-simple-select-autowidth-label">Status</InputLabel>
        <Select
          labelId="demo-simple-select-autowidth-label"
          id="demo-simple-select-autowidth"
          value={props.status}
          onChange={props.changeStatus}
          label="Status"
          style={{ minWidth: 120 }}
        >
          <MenuItem value={0}>All</MenuItem>
          <MenuItem value={10}>New</MenuItem>
          <MenuItem value={20}>Paid</MenuItem>
          <MenuItem value={30}>Done</MenuItem>
        </Select>
      </FormControl>
    </div>
  );
}

OrderStatusSelect.propTypes = {
  status: PropTypes.number,
  changeStatus: PropTypes.func
}

export function OrderLineStatusSelect(props) {
  const classes = useStyles();
  const [data, setData] = useContext(DataContext);

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
    })
    // .then(response => {
    //   response.json()
    // })
    // .catch(error => console.warn(error));

    return response;
  }

  return (
    <div>
      <FormControl margin={'none'} className={classes.formControl}>
        <Select
          id={props.id}
          order={props.order}
          value={props.orderLineStatus}
          // disabled={props.orderLineStatus === 20}
          onChange={(e) => {
            updateOrderLine(e, props.id)
            .then(response => {
              if (response.status === 200) {
                fetch(`${orderListURL}${props.order}`)
                  .then(response => response.json())
                  .then(orderData => {
                    const orders = data.results.map(
                      order => order.id == props.order ? orderData : order
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
  order: PropTypes.string,
  orderLineStatus: PropTypes.number
}

