import yfinance as yf
import json

def getInfo( symbol, attribute="dummy" ):

  ticker = yf.Ticker(symbol)
  ticker_info = json.loads(json.dumps(ticker.info))

  if attribute == "dummy":
    return ticker_info
  else:
    return ticker_info[attribute]


def getIsin( symbol ):
    ticker = yf.Ticker(symbol)
    return ticker.isin
