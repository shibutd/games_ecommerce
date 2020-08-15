import React from 'react';
import PropTypes from "prop-types";
import Box from '@material-ui/core/Box';
import Table from '@material-ui/core/Table';
import TableBody from '@material-ui/core/TableBody';
import TableCell from '@material-ui/core/TableCell';
import TableContainer from '@material-ui/core/TableContainer';
import TableFooter from '@material-ui/core/TableFooter';
import TableHead from '@material-ui/core/TableHead';
import TableRow from '@material-ui/core/TableRow';
import TablePagination from '@material-ui/core/TablePagination';
import Paper from '@material-ui/core/Paper';
import Row from './Row';
import TablePaginationActions from './TablePaginationActions';

export default function CollapsibleTable(props) {
  const { data, page, rowsPerPage, onChangePage, onChangeRowsPerPage } = props;

  return (
    <TableContainer component={Paper}>
        { data.count ? (
        <>
        <Table aria-label="collapsible table">
          <TableHead>
            <TableRow>
              <TableCell />
              <TableCell>E-mail address</TableCell>
              <TableCell align="right">Billing address</TableCell>
              <TableCell align="right">Shipping address</TableCell>
              <TableCell align="right">Date Added</TableCell>
              <TableCell align="right">Status</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {data.results.map((dataRow) => (
              <Row key={dataRow.id} row={dataRow} />
            ))}
          </TableBody>
          <TableFooter>
            <TableRow>
              <TablePagination
                rowsPerPageOptions={[10, 25, 50]}
                colSpan={8}
                count={data.count}
                rowsPerPage={rowsPerPage}
                page={page}
                SelectProps={{
                  inputProps: { 'aria-label': 'rows per page' },
                  native: true,
                }}
                onChangePage={onChangePage}
                onChangeRowsPerPage={onChangeRowsPerPage}
                ActionsComponent={TablePaginationActions}
              />
            </TableRow>
          </TableFooter>
        </Table>
        </>
        ) : (
        <Box margin={2} display="flex" justifyContent="center">
          <h4><b>No orders :(</b></h4>
        </Box> )
      }
    </TableContainer>
  );
}

CollapsibleTable.propTypes = {
  data: PropTypes.object,
  page: PropTypes.number,
  rowsPerPage: PropTypes.number,
  onChangePage: PropTypes.func,
  onChangeRowsPerPage: PropTypes.func
}

