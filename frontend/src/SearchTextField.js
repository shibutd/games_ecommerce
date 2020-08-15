import React from 'react';
import PropTypes from "prop-types";
import { makeStyles } from '@material-ui/core/styles';
import FormControl from '@material-ui/core/FormControl';
import Input from '@material-ui/core/Input';
import InputLabel from '@material-ui/core/InputLabel';

const useStyles = makeStyles((theme) => ({
  root: {
    '& > *': {
      margin: theme.spacing(1),
    },
  },
}));

export default function SearchTextField(props) {
  const classes = useStyles();

  return (
    <form className={classes.root} noValidate autoComplete="off">
      <FormControl>
        <InputLabel htmlFor="component-simple">E-mail Search</InputLabel>
        <Input
          id="component-simple"
          value={props.searchInput}
          onChange={props.changeSearch}
        />
      </FormControl>
    </form>
  );
}

SearchTextField.propTypes = {
  searchInput: PropTypes.string,
  changeSearch: PropTypes.func
}
