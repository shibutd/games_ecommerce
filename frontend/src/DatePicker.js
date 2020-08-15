import 'date-fns';
import React from 'react';
import PropTypes from "prop-types";
import DateFnsUtils from '@date-io/date-fns';
import {
  MuiPickersUtilsProvider,
  KeyboardDatePicker,
} from '@material-ui/pickers';

export default function DatePicker(props) {

  return (
    <MuiPickersUtilsProvider utils={DateFnsUtils}>
      <KeyboardDatePicker
        //disableToolbar
        variant="inline"
        format="dd/MM/yyyy"
        margin="normal"
        id="date-picker-inline"
        label={props.label}
        value={props.selectedDate}
        onChange={props.changeDate}
        KeyboardButtonProps={{
          'aria-label': 'change date',
        }}
      />
    </MuiPickersUtilsProvider>
  );
}

DatePicker.propTypes = {
  label: PropTypes.string,
  selectedDate: PropTypes.oneOfType([
      PropTypes.string,
      PropTypes.oneOf([null])
  ]),
  changeDate: PropTypes.func
}
