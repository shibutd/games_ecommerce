import React, { useState, useContext, useEffect, useCallback } from 'react';
import Box from '@material-ui/core/Box';
import Grid from '@material-ui/core/Grid';
import CircularProgress from '@material-ui/core/CircularProgress';
import TableContainer from '@material-ui/core/TableContainer';
import Paper from '@material-ui/core/Paper';
import CollapsibleTable from './CollapsibleTable';
import DatePicker from './DatePicker';
import SearchTextField from './SearchTextField';
import OrderStatusSelect from './OrderStatusSelect';
import { orderListURL } from './constants';
import { OrderContext, useUserStaff } from "./context";

export default function Dashboard() {
  const isUserStaff = useUserStaff();
  const [data, setData] = useContext(OrderContext);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [status, setStatus] = useState(0);
  const [fromDate, setFromDate] = useState(null);
  const [toDate, setToDate] = useState(null);
  const [searchInput, setSearchInput] = useState('');

  const getUrl = useCallback(() => {
    const actPage = page + 1;
    const actStatus = (status || '');
    const actFromDate = (fromDate || '');
    const actToDate = (toDate || '');

    return `${orderListURL}?page=${actPage}&page_size=${rowsPerPage}\
&status=${actStatus}&from_date=${actFromDate}&to_date=${actToDate}\
&search=${searchInput}&ordering=-date_added`;
  }, [page, rowsPerPage, status, fromDate, toDate, searchInput]);

  const handleChangePage = (event, newPage) => {
    setPage(newPage);
  }

  const handleChangeRowsPerPage = (event) => {
    const rowsPerPageValue = parseInt(event.target.value, 10);
    setPage(0);
    setRowsPerPage(rowsPerPageValue);
  }

  const handleChangeStatus = (event) => {
    const statusValue = event.target.value;
    setPage(0);
    setStatus(statusValue);
  }

  const convertDate = (date) => {
    const dateDay = date.getDate();
    const dateMonth = date.getMonth() + 1;
    const dateYear = date.getFullYear();
    const dateValue = `${dateYear}-${dateMonth}-${dateDay}`;

    return dateValue;
  }

  const handleChangeFromDate = (date) => {
    setPage(0);
    setFromDate(convertDate(date));
  }

  const handleChangeToDate = (date) => {
    setPage(0);
    setToDate(convertDate(date));
  }

  const handleSearch = (event) => {
    const input = event.target.value;
    setPage(0);
    setSearchInput(input);
  }

  useEffect(() => {
    const abortController = new AbortController();

    const fetchData = async (url) => {

      try {
        const response = await fetch(
          url,
          { signal: abortController.signal }
        )

        if (!response.ok) {
          throw new Error(
            `${response.status} ${response.statusText}`
          );
        }

        const resp = await response.json();

        setData(resp);
        setLoading(false);

      } catch (e) {
        console.log(e);
      }
    };

    fetchData(getUrl());

    return () => {
      abortController.abort();
    }
  }, [getUrl]);

  return (
    <TableContainer component={Paper}>
      { loading ? (
      <Box margin={2} display="flex" justifyContent="center">
        <CircularProgress />
      </Box> ) : (
      <>
      <Grid container justify="center" alignItems="flex-end">
        { isUserStaff && <SearchTextField
          searchInput={searchInput}
          changeSearch={handleSearch}
        /> }
        <DatePicker
          label="From date:"
          selectedDate={fromDate}
          changeDate={handleChangeFromDate}
        />
        <DatePicker
          label="To date:"
          selectedDate={toDate}
          changeDate={handleChangeToDate}
        />
        <OrderStatusSelect
          status={status}
          changeStatus={handleChangeStatus}
        />
      </Grid>
      <CollapsibleTable
        data={data}
        page={page}
        rowsPerPage={rowsPerPage}
        onChangePage={handleChangePage}
        onChangeRowsPerPage={handleChangeRowsPerPage}
      />
      </> )}
    </TableContainer>
  )
}
