import React from 'react';
import PropTypes from "prop-types";
import { makeStyles } from '@material-ui/core/styles';
import InputLabel from '@material-ui/core/InputLabel';
import MenuItem from '@material-ui/core/MenuItem';
import FormControl from '@material-ui/core/FormControl';
import Select from '@material-ui/core/Select';

const useStyles = makeStyles((theme) => ({
  formControl: {
    margin: theme.spacing(1),
  },
  selectEmpty: {
    marginTop: theme.spacing(2),
  },
}));

export default function OrderStatusSelect(props) {
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
