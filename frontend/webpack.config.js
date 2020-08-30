const path = require('path');
var webpack = require('webpack');
const BundleTracker = require('webpack-bundle-tracker')

module.exports = {
    context: __dirname,
    entry: {
        dashboard: './src/AppDashboard.js',
        orders_per_day: './src/AppOrdersPerDay.js',
        most_bought_products: './src/AppMostBoughtProducts.js',
    },
    output: {
        filename: '[name].js',
        path: path.resolve('../assets/bundles/')
    },
    plugins: [
        new BundleTracker({ filename: './webpack-stats.json' }),
    ],
    module: {
        rules: [
            {
                test: /\.js$|jsx/,
                exclude: /node_modules/,
                use: {
                  loader: "babel-loader"
                }
            },
            {
                test: /\.css$/,
                use: [
                  'style-loader',
                  'css-loader'
                ]
            }
        ]
    }
};