# import all libraries useful for this program
import pandas as pd  # pandas for manipulation of data
import math  # math for calculations
import yfinance as yf  # yfinance for retrieving data (more reliable than yahoofinancials)
import datetime as dt  # datetime for retrieving current time
from flask import Flask  # flask for python web application
import warnings  # warnings for suppressing pandas warnings
import argparse  # argparse for command line argument parsing
import json  # json for chart data serialization

# Suppress pandas warnings about chained assignment and future warnings
warnings.filterwarnings('ignore', category=pd.errors.SettingWithCopyWarning)
warnings.filterwarnings('ignore', category=FutureWarning)

# COMMAND LINE ARGUMENT PARSING
def parse_arguments():
    parser = argparse.ArgumentParser(description='Accelerating Dual Momentum Investing Analysis')
    parser.add_argument('--start-date', 
                       type=str, 
                       default='1998-01-01',
                       help='Start date for data retrieval (format: YYYY-MM-DD, default: 1998-01-01)')
    return parser.parse_args()

# Parse command line arguments
args = parse_arguments()

# VIDEO 2: DATA GRABBING (FROM YFINANCE)
# these raw data is collected for further calculations in this program
all_tickers = ["SPY", "VINEX", "VUSTX"]
def get_data(start_date_str):
    close_prices = pd.DataFrame()
    # get data from specified start date to today
    end_date = dt.date.today()
    try:
        beg_date = dt.datetime.strptime(start_date_str, '%Y-%m-%d').date()
    except ValueError:
        print(f"Invalid date format: {start_date_str}. Using default date 1998-01-01")
        beg_date = dt.date(1998, 1, 1)
    # to get data of a specific range, please replace the two lines above with: (example, the two lines below)
    # beg_date = dt.date(2014, 6, 30)
    # end_date = dt.date(2016, 6, 30)
    # SPY:      S&P 500
    # VINEX:    Vanguard International Explorer
    # VUSTX:    Vanguard Long-term US Treasury
    
    # Create a list to store data for each ticker
    ticker_data = []
    
    # extracting stock data (historical close price) for the stocks identified
    print(f"Downloading data from {beg_date} to {end_date} (start date specified: {start_date_str})")
    for ticker in all_tickers:
        try:
            print(f"Downloading data for {ticker}...")
            # Download data using yfinance
            stock_data = yf.download(ticker, start=beg_date, end=end_date, interval="1mo", progress=False)
            
            if not stock_data.empty:
                # Reset index to get Date as a column
                stock_data = stock_data.reset_index()
                
                # Debug: print the columns to understand the structure
                print(f"Columns for {ticker}: {stock_data.columns.tolist()}")
                
                # Handle MultiIndex columns - flatten them first
                if isinstance(stock_data.columns, pd.MultiIndex):
                    # Flatten the MultiIndex columns
                    stock_data.columns = ['_'.join(col).strip('_') for col in stock_data.columns]
                
                # Handle different column names that might be returned
                adj_close_col = None
                close_cols = [col for col in stock_data.columns if 'close' in col.lower() and ticker.upper() in col.upper()]
                
                if close_cols:
                    adj_close_col = close_cols[0]  # Take the first matching close column
                elif 'Close' in stock_data.columns:
                    adj_close_col = 'Close'
                elif 'Adj Close' in stock_data.columns:
                    adj_close_col = 'Adj Close'
                else:
                    print(f"Could not find close price column for {ticker}")
                    print(f"Available columns: {stock_data.columns.tolist()}")
                    continue
                
                # Format the data to match original structure
                temp = pd.DataFrame({
                    'Date': stock_data['Date'].dt.strftime('%Y-%m-%d'),
                    ticker: stock_data[adj_close_col].values  # Use .values to avoid index issues
                })
                
                ticker_data.append(temp)
                print(f"Successfully downloaded {len(temp)} data points for {ticker}")
            else:
                print(f"No data available for {ticker}")
                
        except Exception as e:
            print(f"Error downloading data for {ticker}: {str(e)}")
            continue
    
    # Merge all ticker data on Date
    if ticker_data:
        close_prices = ticker_data[0]
        for i in range(1, len(ticker_data)):
            close_prices = pd.merge(close_prices, ticker_data[i], on='Date', how='outer')
        
        # Sort by date and reset index
        close_prices = close_prices.sort_values('Date').reset_index(drop=True)
        close_prices.dropna(axis=0, inplace=True)
        print(f"Final dataset shape: {close_prices.shape}")
        print(f"Columns: {close_prices.columns.tolist()}")
        return close_prices
    else:
        print("No data was successfully downloaded for any ticker")
        # Return empty DataFrame with expected structure
        return pd.DataFrame(columns=['Date'] + all_tickers)
# Note that: "close_prices"(as defined locally above) is now "data" globally
# Store the data retrieved as "data". We will call the retrieved data as "data" from now on.
data = get_data(args.start_date)  # "data" containing rows: "Date", "SPY", "VINEX" and "VUSTX"

# VIDEO 3: INITIALIZATION (OF NEW ATTRIBUTES & CONSTANTS)
n1, n2, n3 = 1, 3, 6
data_columns = [f"{n1} month return- SPY", f"{n1} month return- VINEX",
                f"{n1} month return- VUSTX", f"{n2} month return- SPY",
                f"{n2} month return- VINEX", f"{n2} month return- VUSTX",
                f"{n3} month return- SPY", f"{n3} month return- VINEX",
                f"{n3} month return- VUSTX", "total return- SPY",
                "total return- VINEX", "total return- VUSTX"]
for data_column in data_columns: data[data_column] = 0.0
data["SPY > VINEX"], data["SPY > VUSTX"], data["VINEX > VUSTX"] \
    = False, False, False
data["Output"], data["Benchmark"] = "", 0

# VIDEO 4: SCORE CALCULATION I (CALCULATE RETURNS OF DIFFERENT PERIODS)
# calculate 1,3,6-monthly & total monthly returns of different indexes
for i in range(0, len(data["SPY"] - 1)):  # for rows in data retrieved
    # calculate 1-monthly returns of different indexes
    for ticker in all_tickers:
        if (i - 1) < 0:  # entry 0 defined as 0.0
            data[f"{n1} month return- " + ticker][i] = 0.0
        else:
            data[f"{n1} month return- " + ticker][i] = (data[ticker][i] - data[ticker][i - 1]) / data[ticker][i - 1]
        # calculate 3-monthly returns of different indexes
        for n in [n2, n3]:
            if (i - (n - 1)) < 0:  # entry 0 defined as 0.0
                data[f"{n} month return- " + ticker][i] = 0.0
            else:
                data[f"{n} month return- " + ticker][i] = (data[ticker][i] - data[ticker][i - (n - 1)]) / \
                                                          data[ticker][i - (n - 1)]
    # calculate total returns of different indexes
    for ticker in all_tickers:
        data["total return- " + ticker][i] = data[f"{n1} month return- " + ticker][i] + \
                                             data[f"{n2} month return- " + ticker][i] + \
                                             data[f"{n3} month return- " + ticker][i]
    # use total returns to generate conditional signals
    data["SPY > VINEX"][i] = (data["total return- SPY"][i] >= data["total return- VINEX"][i])
    data["SPY > VUSTX"][i] = (data["total return- SPY"][i] >= data["total return- VUSTX"][i])
    data["VINEX > VUSTX"][i] = (data["total return- VINEX"][i] >= data["total return- VUSTX"][i])

# VIDEO 5: SCORE CALCULATION II (MORE CALCULATIONS)
# Define initial capital
initial_capital = 10000
# remove first n1 values which are equal to 0
data = data[n3:].reset_index(drop=True)
data["Benchmark"][0] = initial_capital / (data["SPY"][0]) * data["SPY"][0]
# change "Output" value depending out total returns
if data["SPY > VINEX"][0]:
    data["Output"][0] = "SPY" if 0 < data["total return- SPY"][0] else "VUSTX"
else:
    data["Output"][0] = "VINEX" if data["total return- VINEX"][0] > 0 else "VUSTX"
# calculate benchmark values
for i in range(1, len(data["SPY"] - 1)): data["Benchmark"][i] = initial_capital / (data["SPY"][0]) * (data["SPY"][i])

# VIDEO 6: SIGNALS I (CREATE BUY SIGNALS)
for i in range(1, len(data["SPY"] - 1)):
    # different cases of signals
    if data["SPY > VINEX"][i]:
        if data["total return- SPY"][i] > 0:
            data["Output"][i] = "Keep SPY" \
                if data["Output"][i - 1] == "SPY" or data["Output"][i - 1] == "Keep SPY" else "SPY"
        else:
            data["Output"][i] = "Keep VUSTX" \
                if data["Output"][i - 1] == "VUSTX" or data["Output"][i - 1] == "Keep VUSTX" else "VUSTX"
    else:
        if data["total return- VINEX"][i] > 0:
            if data["Output"][i - 1] == "VINEX" or data["Output"][i - 1] == "Keep VINEX":
                data["Output"][i] = "Keep VINEX"
            else:
                data["Output"][i] = "VINEX"
        else:
            if data["Output"][i - 1] == "VUSTX" or data["Output"][i - 1] == "Keep VUSTX":
                data["Output"][i] = "Keep VUSTX"
            else:
                data["Output"][i] = "VUSTX"

# VIDEO 7: SIGNALS II (STORE THE BUY SIGNALS & MORE CALCULATIONS)
# create new dataset ("buy_signals") with only buy signals (remove Keep signals)
buy_signals = data.drop(data[data.Output == "Keep VUSTX"].index).drop(data[data.Output == "Keep SPY"].index) \
    .drop(data[data.Output == "Keep VINEX"].index).reset_index(drop=True)
# columns with qty amount to buy
bs_columns = ["Qty VUSTX", "Qty SPY", "Qty VINEX", "VUSTX Buy Amount", "VUSTX Sell Amount", "SPY Buy Amount",
              "SPY Sell Amount", "VINEX Buy Amount", "VINEX Sell Amount", "Buy Amount", "Sell Amount",
              "P/L", "Cash Account", "realised_val"]
for bs_column in bs_columns: buy_signals[bs_column] = 0.0
for ticker in all_tickers:
    if buy_signals["Output"][0] == ticker:
        buy_signals["Qty " + ticker][0] = math.floor(initial_capital / buy_signals[ticker][0])
        buy_signals[ticker + " Buy Amount"][0] = buy_signals["Qty " + ticker][0] * buy_signals[ticker][0]
# total buy amount
buy_signals["Buy Amount"][0] = buy_signals["VUSTX Buy Amount"][0] + buy_signals["SPY Buy Amount"][0] + \
                               buy_signals["VINEX Buy Amount"][0]
buy_signals["Cash Account"][0] = initial_capital - buy_signals["Buy Amount"][0]
# realised value is cash value of assets + cash account at hand
buy_signals["realised_val"][0] = buy_signals["Buy Amount"][0] + buy_signals["Cash Account"][0]
# buy and sell amount for individual assets
for i in range(1, len(buy_signals["Output"])):
    # sell amount for VUSTX
    for ticker in all_tickers:
        if buy_signals["Output"][i - 1] == ticker:
            buy_signals[ticker + " Sell Amount"][i] = buy_signals["Qty " + ticker][i - 1] * buy_signals[ticker][i]
    # total sell amount
    buy_signals["Sell Amount"][i] = buy_signals["VUSTX Sell Amount"][i] + buy_signals["SPY Sell Amount"][i] + \
                                    buy_signals["VINEX Sell Amount"][i]
    for ticker in all_tickers:
        if buy_signals["Output"][i] == ticker:
            buy_signals["Qty " + ticker][i] = math.floor((buy_signals["Cash Account"][i - 1] +
                                                          buy_signals["Sell Amount"][i]) / buy_signals[ticker][i])
            buy_signals[ticker + " Buy Amount"][i] = buy_signals["Qty " + ticker][i] * buy_signals[ticker][i]
    # total buy amount
    buy_signals["Buy Amount"][i] = buy_signals["VUSTX Buy Amount"][i] + buy_signals["SPY Buy Amount"][i] + \
                                   buy_signals["VINEX Buy Amount"][i]
    # cash account is the remaining balance after buying Whole shares
    buy_signals["Cash Account"][i] = buy_signals["Cash Account"][i - 1] - buy_signals["Buy Amount"][i] + \
                                     buy_signals["Sell Amount"][i]
    # calculate profit and loss
    buy_signals["P/L"][i] = buy_signals["Sell Amount"][i] - buy_signals["Buy Amount"][i - 1]
    # realised value is cash value of assets + cash account at hand + profit/loss
    buy_signals["realised_val"][i] = buy_signals["realised_val"][i - 1] + buy_signals["P/L"][i] + \
                                     buy_signals["Cash Account"][i]
buy_signals["Port_val"] = initial_capital
# calculate portfolio value which tracks the real time value of assets in the portfolio
for i in range(1, len(buy_signals["realised_val"])):
    buy_signals["Port_val"][i] = (buy_signals["Qty VUSTX"][i] * buy_signals["VUSTX"][i]) + \
                                 (buy_signals["Qty SPY"][i] * buy_signals["SPY"][i]) + \
                                 (buy_signals["Qty VINEX"][i] * buy_signals["VINEX"][i]) + \
                                 buy_signals["Cash Account"][i]

# VIDEO 8: RESULTS SUMMARIZATION I
# initialize all elements as 0.0 (we may change it to other numbers later on)
results = data.copy()
results_columns_1 = ["Qty VUSTX", "Qty SPY", "Qty VINEX", "VUSTX Buy Amount", "SPY Buy Amount", "VINEX Buy Amount",
                     "VUSTX Sell Amount", "SPY Sell Amount", "VINEX Sell Amount", "Buy Amount", "Sell Amount",
                     "P/L", "realised_val", "Cash Account"]
results_columns_2 = ["Port_val", "PortMax", "DrawDown", "%change monthly", "%change benchmark", "Qty"]
for results_column in results_columns_1 + results_columns_2: results[results_column] = 0.0
# copy buy signals to results
for i in range(0, len(buy_signals["Output"])):
    for j in range(0, len(data["Output"])):
        if buy_signals["Date"][i] == data["Date"][j]:
            for results_column_1 in results_columns_1:
                results[results_column_1][j] = buy_signals[results_column_1][i]
# fill in the gaps for the data in results, as buy_signals does not have all the rows
for i in range(1, len(results["realised_val"])):
    results["realised_val"][i] = results["realised_val"][i - 1] if results["realised_val"][i] == 0 \
        else results["realised_val"][i]
    for ticker in all_tickers:
        if results["Output"][i] == "Keep " + ticker:
            results["Qty " + ticker][i] = results["Qty " + ticker][i - 1]
        elif results["Output"][i] == ticker:
            results["Qty " + ticker] = results["Qty " + ticker]
        else:
            results["Qty " + ticker][i] = 0
    results["Qty"][i] = results["Qty SPY"][i] + results["Qty VINEX"][i] + results["Qty VUSTX"][i]
    if results["Cash Account"][i] == 0 and i != 0:
        results["Cash Account"][i] = results["Cash Account"][i - 1]
results["Port_val"][0] = initial_capital
results["PortMax"][0] = initial_capital
for i in range(1, len(results["realised_val"])):
    results["Port_val"][i] = (results["Qty VUSTX"][i] * results["VUSTX"][i]) + (
            results["Qty SPY"][i] * results["SPY"][i]) + (results["Qty VINEX"][i] * results["VINEX"][i])
    curr_set2 = results["Port_val"][0:i + 1]
    results["PortMax"][i] = curr_set2.max()
    results["DrawDown"][i] = (results["Port_val"][i] - results["PortMax"][i]) / results["PortMax"][i]
# calculate percent changes in porfolio and benchmark on monthly basis
results.loc[0, "%change monthly"] = 0.0
results.loc[0, "%change benchmark"] = 0.0
for i in range(1, len(results["realised_val"])):
    # percent change daily
    results.loc[i, "%change monthly"] = (results["Port_val"][i] - results["Port_val"][i - 1]) / \
                                       results["Port_val"][i - 1]
    #    results["%change monthly"] = results["Port_val"].pct_change(1)
    results.loc[i, "%change benchmark"] = (results["Benchmark"][i] - results["Benchmark"][i - 1]) / \
                                         results["Benchmark"][i - 1]


# VIDEO 9: RESULTS SUMMARIZATION II
# prepare the string for the final result
# list of attributes in the data(index 0), buy_signals(index 1) and results(index 2) dictionaries
data_attr = [["SPY", "VINEX", "VUSTX", f"{n1} month return- SPY", f"{n1} month return- VINEX",
              f"{n1} month return- VUSTX", f"{n2} month return- SPY", f"{n2} month return- VINEX",
              f"{n2} month return- VUSTX", f"{n3} month return- SPY", f"{n3} month return- VINEX",
              f"{n3} month return- VUSTX", "total return- SPY", "total return- VINEX", "total return- VUSTX",
              "SPY > VINEX", "SPY > VUSTX", "VINEX > VUSTX", "Output", "Benchmark"],
             ["Qty VUSTX", "Qty SPY", "Qty VINEX", "VUSTX Buy Amount", "VUSTX Sell Amount", "SPY Buy Amount",
              "SPY Sell Amount", "VINEX Buy Amount", "VINEX Sell Amount", "Buy Amount", "Sell Amount", "P/L",
              "Cash Account", "realised_val", "Output"],
             ["Qty VUSTX", "Qty SPY", "Qty VINEX", "VUSTX Buy Amount", "SPY Buy Amount", "VINEX Buy Amount",
              "VUSTX Sell Amount", "SPY Sell Amount", "VINEX Sell Amount", "Buy Amount", "Sell Amount", "realised_val",
              "P/L", "Port_val", "Cash Account", "PortMax", "DrawDown", "%change monthly", "%change benchmark", "Qty"]]
# calculate data 2 dates
date2 = []
for i in range(0, len(data["Output"])):
    if data["Output"][i] in all_tickers: date2.append(data["Date"][i])
# construct the string of html codes (table)
def format_value(value):
    """Format numeric values to 2 decimal places, keep strings as-is"""
    try:
        # Try to convert to float and format
        if isinstance(value, (int, float)):
            return f"{float(value):.2f}"
        elif isinstance(value, str) and value.replace('.', '').replace('-', '').replace('+', '').isdigit():
            return f"{float(value):.2f}"
        else:
            return str(value)
    except (ValueError, TypeError):
        return str(value)

def generate_chart_data():
    """Generate data for the performance comparison chart"""
    chart_data = {
        'dates': [],
        'portfolio_values': [],
        'benchmark_values': []
    }
    
    # Use results data for the chart - sample every few data points to avoid browser clogging
    sample_rate = max(1, len(results["Date"]) // 100)  # Sample to max 100 points
    
    for i in range(0, len(results["Date"]), sample_rate):
        chart_data['dates'].append(results["Date"][i])
        
        # Ensure we're working with reasonable portfolio values
        port_val = float(results["Port_val"][i])
        benchmark_val = float(results["Benchmark"][i])
        
        # Add some debugging output
        if i == 0:
            print(f"First data point - Portfolio: {port_val:,.2f}, Benchmark: {benchmark_val:,.2f}")
        elif i == len(results["Date"]) - 1:
            print(f"Last data point - Portfolio: {port_val:,.2f}, Benchmark: {benchmark_val:,.2f}")
        
        chart_data['portfolio_values'].append(port_val)
        chart_data['benchmark_values'].append(benchmark_val)
    
    # Add the last point if we didn't get it due to sampling
    if (len(results["Date"]) - 1) % sample_rate != 0:
        last_idx = len(results["Date"]) - 1
        chart_data['dates'].append(results["Date"][last_idx])
        chart_data['portfolio_values'].append(float(results["Port_val"][last_idx]))
        chart_data['benchmark_values'].append(float(results["Benchmark"][last_idx]))
    
    print(f"Chart data points: {len(chart_data['dates'])}")
    return json.dumps(chart_data)

def generate_statistics_table(stats):
    """Generate HTML for the statistics comparison table"""
    html = "<table class='statistics-table'>"
    html += "<tr><th>Metric</th><th>Dual Momentum Portfolio</th><th>S&P 500 Buy & Hold</th></tr>"
    
    html += f"<tr><td class='metric-name'>Initial Value</td><td>${stats['initial_value']:,.2f}</td><td>${stats['initial_value']:,.2f}</td></tr>"
    html += f"<tr><td class='metric-name'>Final Value</td><td>${stats['final_portfolio']:,.2f}</td><td>${stats['final_benchmark']:,.2f}</td></tr>"
    html += f"<tr><td class='metric-name'>Total Return</td><td>{stats['portfolio_total_return']:.2f}%</td><td>{stats['benchmark_total_return']:.2f}%</td></tr>"
    html += f"<tr><td class='metric-name'>Annualized Return</td><td>{stats['portfolio_annual_return']:.2f}%</td><td>{stats['benchmark_annual_return']:.2f}%</td></tr>"
    html += f"<tr><td class='metric-name'>Maximum Drawdown</td><td>{stats['portfolio_max_drawdown']:.2f}%</td><td>{stats['benchmark_max_drawdown']:.2f}%</td></tr>"
    html += f"<tr><td class='metric-name'>Time Period</td><td>{stats['years']:.1f} years</td><td>{stats['years']:.1f} years</td></tr>"
    html += f"<tr><td class='metric-name'>Total Number of Trades</td><td>{stats['total_trades']}</td><td>1 (Buy & Hold)</td></tr>"
    html += f"<tr><td class='metric-name'>SPY Trades</td><td>{stats['spy_trades']}</td><td>-</td></tr>"
    html += f"<tr><td class='metric-name'>VINEX Trades</td><td>{stats['vinex_trades']}</td><td>-</td></tr>"
    html += f"<tr><td class='metric-name'>VUSTX Trades</td><td>{stats['vustx_trades']}</td><td>-</td></tr>"
    
    html += "</table>"
    return html

def calculate_statistics():
    """Calculate key performance statistics"""
    # Count trades for each instrument
    spy_trades = sum(1 for output in buy_signals["Output"] if "SPY" in output and "Keep" not in output)
    vinex_trades = sum(1 for output in buy_signals["Output"] if "VINEX" in output and "Keep" not in output)
    vustx_trades = sum(1 for output in buy_signals["Output"] if "VUSTX" in output and "Keep" not in output)
    total_trades = spy_trades + vinex_trades + vustx_trades
    
    # Calculate annual performance - add validation
    initial_portfolio = float(results["Port_val"][0])
    final_portfolio = float(results["Port_val"][len(results["Port_val"]) - 1])
    initial_benchmark = float(results["Benchmark"][0])
    final_benchmark = float(results["Benchmark"][len(results["Benchmark"]) - 1])
    
    # Debug output to check values
    print(f"Portfolio: Initial ${initial_portfolio:,.2f}, Final ${final_portfolio:,.2f}")
    print(f"Benchmark: Initial ${initial_benchmark:,.2f}, Final ${final_benchmark:,.2f}")
    
    # Validate that we have reasonable values
    if initial_portfolio <= 0 or final_portfolio <= 0 or initial_benchmark <= 0 or final_benchmark <= 0:
        print("Warning: Invalid portfolio or benchmark values detected!")
        return None
    
    # Calculate time period in years
    start_date = results["Date"][0]
    end_date = results["Date"][len(results["Date"]) - 1]
    years = (dt.datetime.strptime(end_date, '%Y-%m-%d') - dt.datetime.strptime(start_date, '%Y-%m-%d')).days / 365.25
    
    # Annualized returns
    portfolio_annual_return = ((final_portfolio / initial_portfolio) ** (1/years) - 1) * 100
    benchmark_annual_return = ((final_benchmark / initial_benchmark) ** (1/years) - 1) * 100
    
    # Total returns
    portfolio_total_return = ((final_portfolio / initial_portfolio) - 1) * 100
    benchmark_total_return = ((final_benchmark / initial_benchmark) - 1) * 100
    
    # Max drawdown (already calculated in results)
    portfolio_max_drawdown = min(results["DrawDown"]) * 100  # Convert to percentage
    
    # Calculate benchmark drawdown
    benchmark_drawdown = []
    benchmark_max = initial_benchmark
    for i in range(len(results["Benchmark"])):
        current_val = float(results["Benchmark"][i])
        if current_val > benchmark_max:
            benchmark_max = current_val
        drawdown = (current_val - benchmark_max) / benchmark_max
        benchmark_drawdown.append(drawdown)
    
    benchmark_max_drawdown = min(benchmark_drawdown) * 100  # Convert to percentage
    
    return {
        'spy_trades': spy_trades,
        'vinex_trades': vinex_trades,
        'vustx_trades': vustx_trades,
        'total_trades': total_trades,
        'portfolio_annual_return': portfolio_annual_return,
        'benchmark_annual_return': benchmark_annual_return,
        'portfolio_total_return': portfolio_total_return,
        'benchmark_total_return': benchmark_total_return,
        'portfolio_max_drawdown': portfolio_max_drawdown,
        'benchmark_max_drawdown': benchmark_max_drawdown,
        'years': years,
        'initial_value': initial_portfolio,
        'final_portfolio': final_portfolio,
        'final_benchmark': final_benchmark
    }

def gen_data_str(data_n, n):
    ret_str = "<table class='data-table'>"
    
    # Create header row with Date and all attributes
    ret_str += "<tr class='header-row'><th>Date</th>"
    for attr in data_attr[n - 1]:
        ret_str += "<th>" + str(attr) + "</th>"
    ret_str += "</tr>"
    
    # Get the dates for this table type
    dates_to_use = []
    if n == 1 or n == 3:
        dates_to_use = data["Date"]
    elif n == 2:
        dates_to_use = date2
    
    # Create one row per date with all attribute values
    for i in range(len(dates_to_use)):
        ret_str += "<tr><td class='date-cell'>" + str(dates_to_use[i]) + "</td>"
        for attr in data_attr[n - 1]:
            if attr in data_n and i < len(data_n[attr]):
                formatted_value = format_value(data_n[attr][i])
                ret_str += "<td class='data-cell'>" + formatted_value + "</td>"
            else:
                ret_str += "<td class='data-cell'>-</td>"  # Placeholder for missing data
        ret_str += "</tr>"
    
    ret_str += "</table>"
    return ret_str
# html codes of tables containing different sets of data, including header, result, and tables
css_styles = """
<style>
    body {
        font-family: 'Courier New', 'Monaco', 'Lucida Console', monospace;
        margin: 20px;
        background-color: #f5f5f5;
    }
    
    .main-title {
        text-align: center;
        font-size: 28px;
        font-weight: bold;
        color: #2c3e50;
        margin-bottom: 20px;
    }
    
    .summary {
        font-size: 16px;
        font-weight: bold;
        color: #34495e;
        margin-bottom: 30px;
        padding: 15px;
        background-color: #ecf0f1;
        border-left: 4px solid #3498db;
    }
    
    .table-title {
        font-size: 18px;
        font-weight: bold;
        color: #2c3e50;
        margin-top: 30px;
        margin-bottom: 10px;
    }
    
    .data-table {
        border-collapse: collapse;
        width: 100%;
        margin-bottom: 30px;
        background-color: white;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    
    .header-row {
        background-color: #34495e;
        color: white;
    }
    
    .header-row th {
        padding: 12px 8px;
        text-align: center;
        font-weight: bold;
        border: 1px solid #2c3e50;
    }
    
    .data-cell, .date-cell {
        padding: 8px;
        text-align: right;
        border: 1px solid #bdc3c7;
        font-size: 12px;
    }
    
    .date-cell {
        text-align: center;
        background-color: #ecf0f1;
        font-weight: bold;
    }
    
    .data-table tr:nth-child(even) {
        background-color: #f8f9fa;
    }
    
    .data-table tr:hover {
        background-color: #e8f4f8;
    }
    
    .chart-container {
        margin: 30px 0;
        background-color: white;
        padding: 20px;
        border-radius: 8px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    
    #performanceChart {
        width: 100%;
        height: 400px;
        max-height: 400px;
    }
    
    .statistics-table {
        border-collapse: collapse;
        width: 100%;
        margin-bottom: 30px;
        background-color: white;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    
    .statistics-table th {
        padding: 12px;
        text-align: center;
        font-weight: bold;
        border: 1px solid #2c3e50;
        background-color: #34495e;
        color: white;
    }
    
    .statistics-table td {
        padding: 10px;
        text-align: center;
        border: 1px solid #bdc3c7;
        font-size: 14px;
    }
    
    .statistics-table tr:nth-child(even) {
        background-color: #f8f9fa;
    }
    
    .metric-name {
        text-align: left !important;
        font-weight: bold;
        background-color: #ecf0f1 !important;
    }
    
    .collapsible {
        background-color: #34495e;
        color: white;
        cursor: pointer;
        padding: 15px;
        width: 100%;
        border: none;
        text-align: left;
        outline: none;
        font-size: 16px;
        font-weight: bold;
        margin-top: 20px;
        font-family: 'Courier New', 'Monaco', 'Lucida Console', monospace;
    }
    
    .collapsible:hover {
        background-color: #2c3e50;
    }
    
    .collapsible:after {
        content: '\\002B';
        color: white;
        font-weight: bold;
        float: right;
        margin-left: 5px;
    }
    
    .active:after {
        content: "\\2212";
    }
    
    .content {
        padding: 0;
        display: none;
        overflow: hidden;
        background-color: #f1f1f1;
    }
    
    .content.show {
        display: block;
        padding: 15px;
    }
</style>
"""

chart_data_json = generate_chart_data()
stats = calculate_statistics()

# Handle case where statistics calculation fails
if stats is None:
    statistics_table = "<p>Error: Could not calculate statistics due to invalid data.</p>"
else:
    statistics_table = generate_statistics_table(stats)

html_content_str = "<html>\n<head>\n<title>Accelerating Dual Momentum Investing</title>\n" + css_styles + \
                   "<script src='https://cdn.jsdelivr.net/npm/chart.js'></script>\n" + \
                   "</head>\n<body>\n<div class='main-title'>Accelerating Dual Momentum Investing</div>\n" + \
                   "<div class='chart-container'>\n" + \
                   "<div class='table-title'>Portfolio Performance vs S&P 500 Buy & Hold:</div>\n" + \
                   "<canvas id='performanceChart'></canvas>\n" + \
                   "</div>\n" + \
                   "<div class='table-title'>Performance Statistics:</div>\n" + \
                   statistics_table + \
                   "<button class='collapsible'>Data Table (Historical Prices and Returns)</button>\n" + \
                   "<div class='content'>" + gen_data_str(data, 1) + "</div>\n" + \
                   "<button class='collapsible'>Buy Signals Table (Trading Actions)</button>\n" + \
                   "<div class='content'>" + gen_data_str(buy_signals, 2) + "</div>\n" + \
                   "<button class='collapsible'>Results Table (Portfolio Performance)</button>\n" + \
                   "<div class='content'>" + gen_data_str(results, 3) + "</div>\n" + \
                   f"""
<script>
const chartData = {chart_data_json};

const ctx = document.getElementById('performanceChart').getContext('2d');
const performanceChart = new Chart(ctx, {{
    type: 'line',
    data: {{
        labels: chartData.dates,
        datasets: [{{
            label: 'Dual Momentum Portfolio',
            data: chartData.portfolio_values,
            borderColor: '#3498db',
            backgroundColor: 'rgba(52, 152, 219, 0.1)',
            borderWidth: 2,
            fill: false,
            tension: 0.1
        }}, {{
            label: 'S&P 500 Buy & Hold',
            data: chartData.benchmark_values,
            borderColor: '#e74c3c',
            backgroundColor: 'rgba(231, 76, 60, 0.1)',
            borderWidth: 2,
            fill: false,
            tension: 0.1
        }}]
    }},
    options: {{
        responsive: true,
        maintainAspectRatio: false,
        animation: {{
            duration: 0 // Disable animations for better performance
        }},
        scales: {{
            x: {{
                title: {{
                    display: true,
                    text: 'Date'
                }},
                ticks: {{
                    maxTicksLimit: 8,
                    maxRotation: 45
                }}
            }},
            y: {{
                title: {{
                    display: true,
                    text: 'Portfolio Value ($)'
                }},
                ticks: {{
                    maxTicksLimit: 8,
                    callback: function(value, index, values) {{
                        if (value >= 1000000) {{
                            return '$' + (value / 1000000).toFixed(1) + 'M';
                        }} else if (value >= 1000) {{
                            return '$' + (value / 1000).toFixed(0) + 'K';
                        }} else {{
                            return '$' + value.toFixed(0);
                        }}
                    }}
                }}
            }}
        }},
        plugins: {{
            title: {{
                display: true,
                text: 'Portfolio Performance Comparison',
                font: {{
                    size: 16
                }}
            }},
            legend: {{
                display: true,
                position: 'top'
            }},
            tooltip: {{
                mode: 'index',
                intersect: false,
                callbacks: {{
                    label: function(context) {{
                        return context.dataset.label + ': $' + context.parsed.y.toLocaleString();
                    }}
                }}
            }}
        }},
        interaction: {{
            mode: 'nearest',
            axis: 'x',
            intersect: false
        }}
    }}
}});

// Collapsible functionality
var coll = document.getElementsByClassName("collapsible");
var i;

for (i = 0; i < coll.length; i++) {{
    coll[i].addEventListener("click", function() {{
        this.classList.toggle("active");
        var content = this.nextElementSibling;
        if (content.style.display === "block") {{
            content.style.display = "none";
        }} else {{
            content.style.display = "block";
        }}
    }});
}}
</script>
""" + \
                   "</body>\n</html>"
# run the web app using Flask
application = Flask(__name__)
application.add_url_rule('/', 'index', (lambda: html_content_str))
if __name__ == "__main__":
    application.debug = True
    application.run()
