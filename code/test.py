import utils
import ib
from sys import argv
import csv
import re
import json
import stock

def test( token ):

    # Get year funds report
    fundsReport = ib.getIBFlex( token, '388465' )

    fundsObject = utils.csvFundsToDividends( fundsReport )

    print(json.dumps(fundsObject))

def testStock( symbol ):

  print(stock.getInfo( symbol ,"dividendRate"))


if __name__ == "__main__":
    
    if len(argv) > 0:
        tick = argv[1]
    
    print(testStock(tick))