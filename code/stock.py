import yfinance as yf
import json

def getPrice( symbol ):
    ticker = yf.Ticker(symbol)
    ticker_info = json.loads(json.dumps(ticker.info))

    return ticker_info["ask"]


def getIsin( symbol ):
    ticker = yf.Ticker(symbol)
    return ticker.isin
