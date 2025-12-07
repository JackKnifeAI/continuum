const path = require('path');
const HtmlWebpackPlugin = require('html-webpack-plugin');
const CopyWebpackPlugin = require('copy-webpack-plugin');
const MiniCssExtractPlugin = require('mini-css-extract-plugin');
const ZipPlugin = require('zip-webpack-plugin');

module.exports = (env) => {
  const browser = env.browser || 'chrome';
  const isProduction = env.mode === 'production';

  return {
    mode: isProduction ? 'production' : 'development',
    devtool: isProduction ? false : 'inline-source-map',

    entry: {
      background: './src/background/service-worker.ts',
      content: './src/content/content.ts',
      popup: './src/popup/index.tsx',
      sidebar: './src/sidebar/index.tsx',
      options: './src/options/index.tsx',
    },

    output: {
      path: path.resolve(__dirname, `dist/${browser}`),
      filename: 'build/[name].js',
      clean: true,
    },

    resolve: {
      extensions: ['.ts', '.tsx', '.js', '.jsx'],
      alias: {
        '@': path.resolve(__dirname, 'src'),
        '@background': path.resolve(__dirname, 'src/background'),
        '@content': path.resolve(__dirname, 'src/content'),
        '@popup': path.resolve(__dirname, 'src/popup'),
        '@sidebar': path.resolve(__dirname, 'src/sidebar'),
        '@options': path.resolve(__dirname, 'src/options'),
        '@shared': path.resolve(__dirname, 'src/shared'),
      },
    },

    module: {
      rules: [
        {
          test: /\.(ts|tsx)$/,
          use: 'ts-loader',
          exclude: /node_modules/,
        },
        {
          test: /\.css$/,
          use: [MiniCssExtractPlugin.loader, 'css-loader'],
        },
      ],
    },

    plugins: [
      new MiniCssExtractPlugin({
        filename: 'build/[name].css',
      }),

      new HtmlWebpackPlugin({
        template: './src/popup/popup.html',
        filename: 'build/popup.html',
        chunks: ['popup'],
      }),

      new HtmlWebpackPlugin({
        template: './src/sidebar/sidebar.html',
        filename: 'build/sidebar.html',
        chunks: ['sidebar'],
      }),

      new HtmlWebpackPlugin({
        template: './src/options/options.html',
        filename: 'build/options.html',
        chunks: ['options'],
      }),

      new CopyWebpackPlugin({
        patterns: [
          {
            from: browser === 'firefox' ? 'manifest.firefox.json' : 'manifest.json',
            to: 'manifest.json',
          },
          {
            from: 'assets',
            to: 'assets',
          },
        ],
      }),

      ...(isProduction
        ? [
            new ZipPlugin({
              path: path.resolve(__dirname, 'packages'),
              filename: `continuum-${browser}-v${require('./package.json').version}.zip`,
            }),
          ]
        : []),
    ],

    optimization: {
      minimize: isProduction,
    },
  };
};
