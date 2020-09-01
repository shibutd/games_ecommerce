import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom';
import "@babel/polyfill";
import Box from '@material-ui/core/Box';
import Paper from '@material-ui/core/Paper';
import CircularProgress from '@material-ui/core/CircularProgress';
import {
  Chart,
  BarSeries,
  ArgumentAxis,
  ValueAxis,
} from '@devexpress/dx-react-chart-material-ui';
import { Animation } from '@devexpress/dx-react-chart';
import DaysPeriodSelect from './DaysPeriodSelect';
import { ordersPerDayURL } from './constants';

export default function AppOrdersPerDay() {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [period, setPeriod] = useState(30);

  const handleChangePeriod = (e) => {
    const periodValue = e.target.value;
    setPeriod(periodValue);
  }

  useEffect(() => {
    const abortController = new AbortController();

    const fetchData = async (days) => {
      const url = `${ordersPerDayURL}${days}`;

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

        const data = await response.json();

        setOrders(data);
        setLoading(false);

      } catch (e) {
        console.log(e);
      }
    };

    setLoading(true);
    fetchData(period);
    
    return () => {
      abortController.abort();
    };
  }, [period]);

  return (
    <>
    <Box p={1} m={1} display="flex" flexDirection="row-reverse">
      <DaysPeriodSelect 
        period={period}
        changePeriod={handleChangePeriod}
      />
    </Box>

    <Paper>
      {loading ? (
      <Box p={1} m={1} display="flex" justifyContent="center">
        <CircularProgress />
      </Box>
      ) : (
      <Chart data={orders}>
        <ArgumentAxis />
        <ValueAxis />

        <BarSeries
          valueField="order_num"
          argumentField="order_day"
        />
        <Animation />
      </Chart>
      )}
    </Paper>
    </>
  );
}

const container = document.getElementById('react-orders-per-day');
ReactDOM.render(<AppOrdersPerDay />, container);
