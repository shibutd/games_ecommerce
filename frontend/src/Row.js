import React, { useState, useContext } from 'react';
import PropTypes from "prop-types";
import { makeStyles } from '@material-ui/core/styles';
import Box from '@material-ui/core/Box';
import Collapse from '@material-ui/core/Collapse';
import IconButton from '@material-ui/core/IconButton';
import Table from '@material-ui/core/Table';
import TableBody from '@material-ui/core/TableBody';
import TableCell from '@material-ui/core/TableCell';
import TableHead from '@material-ui/core/TableHead';
import TableRow from '@material-ui/core/TableRow';
import Typography from '@material-ui/core/Typography';
import KeyboardArrowDownIcon from '@material-ui/icons/KeyboardArrowDown';
import KeyboardArrowUpIcon from '@material-ui/icons/KeyboardArrowUp';
import { OrderLineStatusSelect } from './SimpleSelect';
import { UserContext } from "./context";

const useRowStyles = makeStyles({
  root: {
    '& > *': {
      borderBottom: 'unset',
    }
  },
});

export default function Row(props) {
  const { row } = props;
  const [isUserStaff] = useContext(UserContext);
  const [open, setOpen] = useState(false);

  const classes = useRowStyles();

  return (
    <React.Fragment>
      <TableRow className={classes.root}>
        <TableCell>
          <IconButton aria-label="expand row" size="small" onClick={() => setOpen(!open)}>
            {open ? <KeyboardArrowUpIcon /> : <KeyboardArrowDownIcon />}
          </IconButton>
        </TableCell>
        <TableCell component="th" scope="row">
          {row.user}
        </TableCell>
        <TableCell align="right">{row.shipping_address}</TableCell>
        <TableCell align="right">{row.billing_address}</TableCell>
        <TableCell align="right">{row.date_added}</TableCell>
        <TableCell align="right">{row.status_description}</TableCell>
      </TableRow>
      <TableRow>
        <TableCell style={{ paddingBottom: 0, paddingTop: 0 }} colSpan={6}>
          <Collapse in={open} timeout="auto" unmountOnExit>
            <Box margin={1}>
              <Typography variant="h6" gutterBottom component="div">
                Order details
              </Typography>
              <Table size="small" aria-label="purchases">
                <TableHead>
                  <TableRow>
                    <TableCell>Product</TableCell>
                    <TableCell align="center">Quantity</TableCell>
                    <TableCell align="right">Status</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {row.order_lines.map((lineRow) => (
                    <TableRow key={lineRow.id}>
                      <TableCell>{lineRow.product}</TableCell>
                      <TableCell align="center">{lineRow.quantity}</TableCell>
                      { !isUserStaff ? (
                      <TableCell align="right">
                        {lineRow.status_description}
                      </TableCell>) : (
                      <TableCell align='right'>
                        <OrderLineStatusSelect
                          id={lineRow.id.toString()}
                          order={row.id.toString()}
                          orderLineStatus={lineRow.status}
                        />
                      </TableCell>)}
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </Box>
          </Collapse>
        </TableCell>
      </TableRow>
    </React.Fragment>
  );
}

Row.propTypes = {
  row: PropTypes.object,
}

