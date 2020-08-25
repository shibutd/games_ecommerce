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
  ValueAxis
} from '@devexpress/dx-react-chart-material-ui';
import { Animation } from '@devexpress/dx-react-chart';
import DaysPeriodSelect from './DaysPeriodSelect';
import { mostBoughtProductsURL } from './constants';

export default function AppMostBoughtProducts() {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [period, setPeriod] = useState(30);

  const handleChangePeriod = (e) => {
    const periodValue = e.target.value;
    setPeriod(periodValue);
  }

  useEffect(() => {
    const fetchData = async (days) => {
      const url = `${mostBoughtProductsURL}${days}`;

      try {
        const response = await fetch(url)

        if (!response.ok) {
          throw new Error(
            `${response.status} ${response.statusText}`
          );
        }

        const data = await response.json();

        setProducts(data);
        setLoading(false);

      } catch (e) {
        console.log(e);
      }
    };

    setLoading(true);
    fetchData(period);
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
      <Chart data={products}>
        <ArgumentAxis />
        <ValueAxis />

        <BarSeries
          valueField="purchase_num"
          argumentField="product_name"
        />
        <Animation />
      </Chart>
      )}
    </Paper>
    </>
  );
}

const container = document.getElementById('react-most-bought-products');
ReactDOM.render(<AppMostBoughtProducts />, container);
