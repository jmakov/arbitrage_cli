#TODO add bitstamp, CampBx
"""
Active Markets
NOTE: 
-> regarding ask/bids list orientation:
        - bids: next imminent bid in orderbook and falling
        - asks: next imminent ask in orderbook and raising
-> on HTML parsing:
    1. get absolute path to the elements in Firefox with firebug
    get_bids = '/html/body/div/div[2]/div/section/div/div/table/tr/td/table/tr[2]/td[2]/strong//text()'
    2. REMOVE the "/tbody/" tags in get_bids - the browser writes them!!!
    3. loop over fields
    4. raise error if strange values = html page changed
"""

import sys
import urllib2
import string
import json
import lxml.html
from lxml import etree
import re

BASE_CURRENCY = "USD"

DEPOSIT_BITINSTANT = 0.01 #%
DEPOSIT_MtGoxCode = 0
DEPOSIT_LIBERTY_RESERVE = 1 #%
DEPOSIT_PAXUM = 0

WITHDRAWAL_LIBERTY_RESERVE = 1 #%
WITHDRAWAL_MtGoxCode = 0
WITHDRAWAL_PAXUM = 0
WITHDRAWAL_PAYPAL = 5 #%


def errorFunction(sys_error, generalMsg):
    sys.stderr.write("\n" + generalMsg + "%s\n" % str(sys_error))

def getHtml(url):
    try:
        website = urllib2.urlopen(url)
        return website

    except urllib2.HTTPError, e:
        sys.stderr.write("\nCannot retrieve URL: %s\n" % url)
        sys.stderr.write("\nHTTP Error Code: %s" % str(e.code))

    except urllib2.URLError, e:
        sys.stderr.write("\nCannot retrieve URL: %s\n" % url)
        sys.stderr.write("\nHTTP Error Code: %s" % str(e.reason[1]))
def getExchangeRates(sourceCurrency):
    try:
        if sourceCurrency != BASE_CURRENCY:
            baseUrl = 'http://www.google.com/ig/calculator?hl=en&q='
            website = getHtml(baseUrl + '1' + sourceCurrency + '=?' + BASE_CURRENCY)
            website_html = website.read()
            reObject = re.search(".*rhs: \"(\d\.\d*)", website_html)
            isInBASE_CURRENCY = reObject.group(1)
            return float(isInBASE_CURRENCY)
        else:
            return 1
    except:
        e = sys.exc_info()[1]
        errorFunction(e, "<getExchangeRates>: ")
        sys.stderr.write("\nArg: ")
        sys.stderr.write(sourceCurrency)
        sys.exit()
#expecting list of the form [[price1, amount1],[price2, amount2], ...]
def convertToBASE_CURRENCY(myObject, sourceCurrency):
    if sourceCurrency != BASE_CURRENCY:
        try:
            isInBASE_CURRENCY = getExchangeRates(sourceCurrency)

            lenBids = len(myObject.bids)
            lenAsks = len(myObject.asks)
            for i in xrange(lenBids):
                myObject.bids[i][0] = myObject.bids[i][0] * isInBASE_CURRENCY
            for i in xrange(lenAsks):
                myObject.asks[i][0] = myObject.asks[i][0] * isInBASE_CURRENCY
        except:
            e = sys.exc_info()[1]
            errorFunction(e, "<convertToBASE_CURRENCY>: ")
            sys.exit()
def getPriceFromString(stringData, id_start_tag, offset_start, id_end_tag, offset_end):
    try:
        id_price_field_position = string.find(stringData, id_start_tag)
        price_field_starts = id_price_field_position + offset_start
        price_field_could_end = id_price_field_position + offset_end

        curr_price_field = stringData[price_field_starts: price_field_could_end]
        #print "field:", curr_price_field
        id_price_field_end_position = string.find(curr_price_field, id_end_tag)
        if id_price_field_end_position > 0:
            myPriceString = stringData[price_field_starts: price_field_starts + id_price_field_end_position]
        else:
            myPriceString = stringData[price_field_starts:]
        #print "priceString:", myPriceString

        #check if decimals separated by comma
        comma_position = string.find(myPriceString, ",")
        if comma_position > 0:
            head = myPriceString[0: comma_position]
            tail = myPriceString[comma_position + 1:]
            myPriceString = head + "." + tail

        curr_price = float(myPriceString)
        return curr_price
    except:
        e = sys.exc_info()[1]
        errorFunction(e, "<EXITING><getCurrentPriceFromString>: ")
        sys.exit()
"""
falling sequence for bids
raising sequence for asks
"""
def checkOrientation(myObject):
    try:
        myObject.bids = sorted(myObject.bids, key=lambda item: item[0], reverse=True)         #largest first
        myObject.asks = sorted(myObject.asks, key=lambda item: item[0])         #smallest first
    except:
        e = sys.exc_info()[1]
        errorFunction(e, "<checkOrientation>: ")
#format of input is [[price1, amount1], [price2, amount2]]
def jsonGetBidAskFields(myObject):
    try:
        website = getHtml(myObject.baseUrl + myObject.currency)
        website_html = website.read()
        data = json.loads(website_html)
        asks_string = data['asks']
        bids_string = data['bids']

        #convert string to float
        lenAsks = len(asks_string)
        lenBids = len(bids_string)
        for i in xrange(lenAsks):
            price = float(asks_string[i][0])
            amount = float(asks_string[i][1])
            myObject.asks.append([price, amount])

        for i in xrange(lenBids):
            price = float(bids_string[i][0])
            amount = float(bids_string[i][1])
            myObject.bids.append([price, amount])

        checkOrientation(myObject)
    except:
        e = sys.exc_info()[1]
        problemMaker = myObject.__name__
        errorFunction(e, "<jsonGetBidAskFields>: " + problemMaker)

## exchanges
#####################################################
#####################################################
def getBCHTML(myObject):
    try:
        website = getHtml(myObject.baseUrl + myObject.currency)
        website_html = website.read()
        html = lxml.html.fromstring(website_html)

        #fill myObject.bids/asks
        bids_html = '/html/body/div/div[3]/div[2]/table/tr[*]/td//text()'
        asks_html = '/html/body/div/div[3]/div[3]/table/tr[*]/td//text()'
        bids_data = html.xpath(bids_html)          #[u'6.2600  EUR\xa0\xa0', '0.892 BTC', u'5.583  EUR\xa0\xa0', u'6.2500  EUR\xa0\xa0', '1.500 BTC', u'9.375  
                                                    #[price, vol, total]
        asks_data = html.xpath(asks_html)

        #get bids
        index_pr = 0
        index_vol = 1
        while index_pr < len(bids_data) - 2:
            field_price = bids_data[index_pr]
            index_pr_stop = string.find(field_price, "EUR")
            price_string = field_price[0:index_pr_stop].replace(',', '')
            price = float(price_string)
            index_pr += 3

            field_vol = bids_data[index_vol]
            index_vol_stop = string.find(field_vol, "BTC")
            vol_string = field_vol[0:index_vol_stop].replace(',', '')
            vol = float(vol_string)
            index_vol += 3

            myObject.bids.append([price, vol])

        #get asks
        index_pr = 0
        index_vol = 1
        while index_pr < len(asks_data) - 2:
            field_price = asks_data[index_pr]
            index_pr_stop = string.find(field_price, "EUR")
            price_string = field_price[0:index_pr_stop].replace(',', '')
            price = float(price_string)
            index_pr += 3

            field_vol = asks_data[index_vol]
            index_vol_stop = string.find(field_vol, "BTC")
            vol_string = field_vol[0:index_vol_stop].replace(',', '')
            vol = float(vol_string)
            index_vol += 3

            myObject.asks.append([price, vol])

        #check if orientation right, else list.reverse
        checkOrientation(myObject)
    except:
        e = sys.exc_info()[1]
        errorFunction(e, "<EXITING><getBCHTML>: ")
        sys.exit()
class BitcoinCentral:
    transferDuration = 0  #number of confirmations
    feeDeposit = {"BTC": 0.0005}
    feeWithdrawal = {"BTC": 0.01}
    feeTransaction = 0  #free
    feeDepositDiffCurrency = 0  #0.25 %
    limitsFunds = 1000000  #no limits
    baseUrl = "https://bitcoin-central.net/order_book"
class bcEUR(BitcoinCentral):
    def __init__(self):
        self.asks = []
        self.bids = []
        self.currency = ""
        getBCHTML(self)
        convertToBASE_CURRENCY(self, "EUR")

"""         #escrow, not exchange
def getbtcdeEUROrderbook(myObject):
    try:
        orderbookAsks = "fleft w450"
        orderbookBids = "fright w450"

        website = getHtml(myObject.baseUrl)
        website_html = website.read()
        html = lxml.html.fromstring(website_html)

        #fill myObject.bids
        get_bids = '//article[@class = "' + orderbookBids + '"]//table//tr//node()[text()]'
        fields = html.xpath(get_bids)
        lenFields = len(fields)

        for i in xrange(4, lenFields - 2, 7):
            amountEl = fields[i + 1]
            priceEl = fields[i + 2]

            #format: 5,04 euro_symbol. Ignoring the euro_symbol:
            decoded_from_utf = priceEl.text.encode('ascii', 'ignore')
            amount = getPriceFromString(amountEl.text, "", 0, "(", 100)
            price = getPriceFromString(decoded_from_utf, "", 0, " ", 20)

            myObject.bids.append([price, amount])

        #fill myObject.asks
        get_asks = '//article[@class = "' + orderbookAsks + '"]//table//tr//node()[text()]'
        fields = html.xpath(get_asks)
        lenFields = len(fields)

        for i in xrange(4, lenFields - 2, 7):
            amountEl = fields[i + 1]
            priceEl = fields[i + 2]

            #format: 5,04 euro_symbol. Ignoring the euro_symbol:
            decoded_from_utf = priceEl.text.encode('ascii', 'ignore')
            amount = getPriceFromString(amountEl.text, "", 0, "(", 100)
            price = getPriceFromString(decoded_from_utf, "", 0, " ", 20)

            myObject.asks.append([price, amount])

        #check if orientation right, else list.reverse
        checkOrientation(myObject)
    except:
        e = sys.exc_info()[1]
        errorFunction(e, "<EXITING><getbtcdeEUROrderbook>: ")
        sys.exit()
class BitcoinDe:
    transferDuration = 3 #number of confirmations
    feeTransaction = 0.005
    feeWithdrawal = 0.01 #BTC's
    feeDepositDiffCurrency = 0 #%
    limitsFunds = 0 #$

    baseUrl = "https://www.bitcoin.de/en/market"
class btcdeEUR(BitcoinDe):
    def __init__(self):
        self.asks = []
        self.bids = []
        getbtcdeEUROrderbook(self)
        convertToBASE_CURRENCY(self, "EUR")
"""
#Bitmarket      #escrow, not exchange

#https://btc-e.com/page/2
class Btce:
    transferDuration = 1        #number of confirmations
    feeDeposit = {"BTC": 0.0005,
                    "LibertyReserve": DEPOSIT_LIBERTY_RESERVE,
                   "Paxum": DEPOSIT_PAXUM}
    feeWithdrawal = {"BTC": 0.01,   #BTC's
                     "LibertyReserve": WITHDRAWAL_LIBERTY_RESERVE,
                     "Paxum": WITHDRAWAL_PAXUM,
                     "PayPal": WITHDRAWAL_PAYPAL}
    feeTransaction = 0.002      #1 = 100%
    feeDepositDiffCurrency = 0  #%
    limitsFundsBTC = 501        #??
    baseUrl = "https://btc-e.com/api/"
class btceUSD(Btce):
    def __init__(self):
        self.asks = []
        self.bids = []
        self.currency = "2/1/depth"
        jsonGetBidAskFields(self)

#https://bitnz.com/fees
class Bitnz:
    transferDuration = 0  #number of confirmations
    feeDeposit = {"BTC": 0.0005}
    feeWithdrawal = {"BTC": 0.0005}
    feeTransaction = 0.005  #0.5 %
    feeDepositDiffCurrency = 0      #NZD free
    limitsFunds = 1000  #$ #??
    baseUrl = "https://bitnz.com/api/0/orderbook"
class bitNZ(Bitnz):
    def __init__(self):
        self.asks = []
        self.bids = []
        self.currency = ""
        jsonGetBidAskFields(self)
        convertToBASE_CURRENCY(self, "NZD")

#API: view funds, view orders, make order, cancel order #https://btcex.com/site/page/api
#https://btcex.com/site/page/rules?language=en
class BTCex:
    transferDuration = 0    #number of confirmations
    feeDeposit = {"BTC": 0.0005,
                "LibertyReserve": DEPOSIT_LIBERTY_RESERVE}
    feeWithdrawal = {"BTC": 0.01,   #BTC's
                     "LibertyReserve": WITHDRAWAL_LIBERTY_RESERVE}
    feeTransaction = 0.0055
    feeDepositDiffCurrency = 0      #%
    limitsFundsBTC = 0
    accBTCaddr = "13UfCmQeJPetKPaMZCbcrMtpr3nQzr1jBy"
    baseUrl = "https://btcex.com/site/orderbooksjson/"
class btcexUSD(BTCex):
    def __init__(self):
        self.asks = []
        self.bids = []
        self.currency = "id/2"
        jsonGetBidAskFields(self)

#https://www.cavirtex.com/home
def getVirtexOrderbook(myObject):
        try:
            website = getHtml(myObject.baseUrl)
            website_html = website.read()
            html = lxml.html.fromstring(website_html)

            orderbookBids = "orderbook_buy"
            orderbookAsks = "orderbook_sell"
            """
            do bids first
            """
            #some fucked up html shit where the most recent element has an extra </b> tag...
            get_most_recent = '//div[contains(@id, "' + orderbookBids + '")]//table/tr/td/node()[text()]'
            get_others = '//div[contains(@id, "' + orderbookBids + '")]//table/tr/node()[text()]'

            fields_most_recent = html.xpath(get_most_recent)
            fields_others = html.xpath(get_others)

            #first field
            amountEl = fields_most_recent[1]
            priceEl = fields_most_recent[2]

            price = float(priceEl.text)
            amount = getPriceFromString(amountEl.text, "", 0, "/", 15)
            myObject.bids.append([price, amount])
            #0: "Created", 1: "Amount", 2: "Price", 3: "Value"; so we're starting from 4
            docLen = len(fields_others)
            for i in xrange(4, docLen - 2, 4):
                amountEl = fields_others[i + 1]
                priceEl = fields_others[i + 2]

                price = float(priceEl.text)
                amount = getPriceFromString(amountEl.text, "", 0, "/", 15)
                myObject.bids.append([price, amount])

            """
            now the same for asks
            """
            get_most_recent = '//div[contains(@id, "' + orderbookAsks + '")]//table/tr/td/node()[text()]'
            get_others = '//div[contains(@id, "' + orderbookAsks + '")]//table/tr/node()[text()]'
            
            fields_most_recent = html.xpath(get_most_recent)
            fields_others = html.xpath(get_others)
            
            #first field
            amountEl = fields_most_recent[1]
            priceEl = fields_most_recent[2]
            
            price = float(priceEl.text)
            amount = getPriceFromString(amountEl.text, "", 0, "/", 15) 
            myObject.asks.append([price, amount])
            
            #other fields
            docLen = len(fields_others)
            for i in xrange(4, docLen - 2, 4):
                amountEl = fields_others[i + 1]
                priceEl = fields_others[i + 2]
    
                price = float(priceEl.text)
                amount = getPriceFromString(amountEl.text, "", 0, "/", 15) 
                myObject.asks.append([price, amount])
            
            #check if orientation right, else list.reverse 
            checkOrientation(myObject)
        except:
            e = sys.exc_info()[1]
            errorFunction(e, "<EXITING><getVirtexOrderbook>: ")
            sys.exit()
class CaVirtex:
    transferDuration = 6  #number of confirmations
    feeDeposit = {"BTC": 0.0005}
    feeWithdrawal = {"BTC": 0.0005}
    feeTransaction = 0.0059
    feeDepositDiffCurrency = 0  #%
    limitsFunds = 5000  #$
    accBTCaddr = "1NC7thtNC3o76L68zEmuwxdjotTrRC1Vch"
    baseUrl = "https://www.cavirtex.com/orderbook"
class virtexCAD(CaVirtex):
    def __init__(self):
        self.asks = []
        self.bids = []

        getVirtexOrderbook(self)
        convertToBASE_CURRENCY(self, "CAD")

#https://cryptoxchange.com/Plan/PlanSelection
#trading API: https://cryptoxchange.com/t/cryptoapi
#is like a dictionary: {price:2332, amount:87689}
def jsonGetCryptoBidAskFields(myObject, currency):
    try:
        website = getHtml(myObject.baseUrl + currency)
        website_html = website.read()
        data = json.loads(website_html)
        asks_string = data['asks']
        bids_string = data['bids']

        #fill asks
        for dictionary in asks_string:
            price_string = dictionary['price']
            amount_string = dictionary['amount']
            price = float(price_string)
            amount = float(amount_string)
            myObject.asks.append([price, amount])

        #fill bids
        for dictionary in bids_string:
            price_string = dictionary['price']
            amount_string = dictionary['amount']
            price = float(price_string)
            amount = float(amount_string)
            myObject.bids.append([price, amount])
        checkOrientation(myObject)
    except:
        e = sys.exc_info()[1]
        errorFunction(e, "<EXITING><jsonGetCryptoBidAskFields>: ")
        sys.exit()
class CryptoXchange:
    transferDuration = 0  #number of confirmations
    feeDeposit = {"BTC": 0.0005,
                    "Mt.Gox code": 0.006,  #%
                    "Bitinstant_LibertyReserve": DEPOSIT_BITINSTANT,
                    "Bitinstant_Paxum": DEPOSIT_BITINSTANT}
    feeWithdrawal = {"BTC": 0.0005,
                    "Mt.Gox code": 0.006}  #%
    feeTransaction = 0.005
    feeDepositDiffCurrency = 0  #%
    limitsFunds = 560  #$
    accBTCaddr = "14bMFCJ2C11bVxdrCkRZZevbBtMVB7Smtg"

    baseUrl = "https://cryptoxchange.com/api/v0/"
    currencyUSD = "data/BTCUSD/orderbook.json"
    currencyAUD = "data/BTCAUD/orderbook.json"
    currencyBTCNMC = "data/BTCNMC/orderbook.json"
    currencyBTCLTC = "data/BTCLTC/orderbook.json"
class cryptoxUSD(CryptoXchange):
    def __init__(self):
        self.asks = []
        self.bids = []
        jsonGetCryptoBidAskFields(self, self.currencyUSD)
class cryptoxAUD(CryptoXchange):
    def __init__(self):
        self.asks = []
        self.bids = []
        jsonGetCryptoBidAskFields(self, self.currencyAUD)
        convertToBASE_CURRENCY(self, "AUD")

#https://intersango.com/fees.php
class Intersango:
    transferDuration = 5  #number of confirmations
    feeDeposit = {"BTC": 0.0005,
                "Paxum": DEPOSIT_PAXUM}
    feeWithdrawal = {"BTC": 0.0005,
                "Paxum": WITHDRAWAL_PAXUM}  #%
    feeTransaction = 0.0095	 #for takers = matched trade
    feeDepositDiffCurrency = 0  #%
    limitsFunds = 0  #$
    accBTCaddr = "1LVsQDYiMxKJ9FZzM8bSEWdqYM94UmTF7h"
    baseUrl = "https://intersango.com/api/depth.php/"
    """
    currency_pair_id is an optional GET parameter to all data api calls
    1 = BTC:GBP
    2 = BTC:EUR
    3 = BTC:USD
    4 = BTC:PLN
    """
class intrsngGBP(Intersango):
    def __init__(self):
        self.asks = []
        self.bids = []
        self.currency = "?currency_pair_id=1"
        jsonGetBidAskFields(self)
        convertToBASE_CURRENCY(self, "GBP")
class intrsngEUR(Intersango):
    def __init__(self):
        self.asks = []
        self.bids = []
        self.currency = "?currency_pair_id=2"
        jsonGetBidAskFields(self)
        convertToBASE_CURRENCY(self, "EUR")
class intrsngUSD(Intersango):
    def __init__(self):
        self.asks = []
        self.bids = []
        self.currency = "?currency_pair_id=3"
        jsonGetBidAskFields(self)
class intrsngPLN(Intersango):
    def __init__(self):
        self.asks = []
        self.bids = []
        self.currency = "?currency_pair_id=4"
        jsonGetBidAskFields(self)
        convertToBASE_CURRENCY(self, "PLN")

#https://imcex.com/
def getImcexHTML(myObject):
    try:
        website = getHtml(myObject.baseUrl + myObject.currency)
        website_html = website.read()
        html = lxml.html.fromstring(website_html)

        #fill myObject.bids
        #get_bids = '//article[@class = "' + orderbookBids + '"]//table//tr//node()[text()]'
        vol_html = '/html/body/div/div[2]/div/section/div/div/table/tr/td/table/tr[*]/td[2]/strong//text()'
        price_html = ''
        vol_list = html.xpath(vol_html)
        #since vol_list returns vol of bids and asks
        bids_vol = vol_list[: len(vol_list) / 2]
        asks_vol = vol_list[len(vol_list) / 2:]

        startpos = 2
        for index in xrange(startpos, 22):
            price_html = '/html/body/div/div[2]/div/section/div/div/table/tr/td/table/tr[' + str(index) + ']/td[4]//text()'
            price_list = html.xpath(price_html)         #['\n4.1400 LREUR\n', '\n8.9900 ', 'LREUR', '\n']
            price_bid = float(price_list[0][1:7])
            price_ask = float(price_list[1][1:7])

            myObject.bids.append([price_bid, float(bids_vol[index - startpos])])
            myObject.asks.append([price_ask, float(asks_vol[index - startpos])])

        #check if orientation right, else list.reverse
        checkOrientation(myObject)
    except:
        e = sys.exc_info()[1]
        errorFunction(e, "<EXITING><getImcexHTML>: ")
        sys.exit()
class Imcex:
    transferDuration = 0  #number of confirmations
    feeDeposit = {"BTC": 0.0005}
    feeWithdrawal = {"BTC": 0.0005}
    feeTransaction = 0.001
    feeDepositDiffCurrency = 0
    limitsFunds = 1000  #$ #??
    accBTCaddr = ""
    baseUrl = "https://imcex.com/en/charts/BTC/"
class imcexEUR(Imcex):
    def __init__(self):
        self.asks = []
        self.bids = []
        self.currency = "LREUR"
        getImcexHTML(self)
        convertToBASE_CURRENCY(self, "EUR")
class imcexUSD(Imcex):
    def __init__(self):
        self.asks = []
        self.bids = []
        self.currency = "LRUSD"
        getImcexHTML(self)
        convertToBASE_CURRENCY(self, "USD")

#http://www.mercadobitcoin.com.br/taxas/
def getMrcdHTML(myObject):
    try:
        website = getHtml(myObject.baseUrl + myObject.currency)
        website_html = website.read()
        html = lxml.html.fromstring(website_html)

        #fill myObject.bids/asks
        vol_html = '/html/body/div[3]/div[2]/table/tr/td/div/div[2]/table//text()'
        data_string = html.xpath(vol_html)         #['Volume (BTC)', u'Pre\xe7o (R$)', '3,61005599', '16,48000', '15,32411000', '16,11012', '130,00000000', '16,11010', '0,40540000', '15,75000', '12,00000000', '15,60011', '8,19583300', '15,60000', '4,00000000', '15,15000', '0,10000000', '15,00010', '30,88633790', '14,87100', '0,10000000', '14,50000', 'Volume (BTC)', u'Pre\xe7o (R$)', '85,30000000', '16,49000',

        #check where data for bids/asks begins/ends
        index_start_bidask_field = []       #only 2: for asks, for bids
        for index, item in enumerate(data_string):
            if item == 'Volume (BTC)':
                index_start_bidask_field.append(index)

        """
        print "STOPS: ", index_start_bidask_field
        """

        index = 0
        bids_vol_index = index_start_bidask_field[0] + 2
        bids_price_index = 0
        asks_vol_index = index_start_bidask_field[1] + 2
        asks_price_index = 0
        end_index = index_start_bidask_field[2]
        while bids_vol_index < asks_vol_index - 2:       #since we take two fields at the time
            bids_price_index = bids_vol_index + 1      #offset bods_start_index, then every second field
            vol = float(data_string[bids_vol_index].replace(',', '.'))
            price = float(data_string[bids_price_index].replace(',', '.'))
            myObject.bids.append([price, vol])
            bids_vol_index += 2      #offset bods_start_index, then every second field
            """
            print "\nbids_", asks_vol_index
            print "vol: ", vol
            print "pr: ", price
            """

        while asks_vol_index < end_index - 2:
            asks_price_index = asks_vol_index + 1
            vol = float(data_string[asks_vol_index].replace(',', '.'))
            price = float(data_string[asks_price_index].replace(',', '.'))
            myObject.asks.append([price, vol])
            asks_vol_index += 2
            """
            print "asks_", asks_vol_index
            print "\nvol: ", data_string[asks_vol_index]
            print "pr: ", data_string[asks_price_index]
            """
        #check if orientation right, else list.reverse
        checkOrientation(myObject)
    except:
        e = sys.exc_info()[1]
        errorFunction(e, "<EXITING><getMrcdHTML>: ")
        sys.exit()
class Mrcd:
    transferDuration = 0  #number of confirmations
    feeDeposit = {"BTC": 0.0005}
    feeWithdrawal = {"BTC": 0.0005}
    feeTransaction = 0.006  #0.6 %
    feeDepositDiffCurrency = 0.016
    limitsFunds = 0
    accBTCaddr = ""
    baseUrl = "http://www.mercadobitcoin.com.br/mercado/"
class mrcdBRL(Mrcd):
    def __init__(self):
        self.asks = []
        self.bids = []
        self.currency = ""
        getMrcdHTML(self)
        convertToBASE_CURRENCY(self, "BRL")

#https://mtgox.com/fee-schedule
class Mtgox:
    transferDuration = 0  #number of confirmations
    feeDeposit = {"BTC": 0.0005,
                    "Mt.Gox code": DEPOSIT_MtGoxCode,    #Mt.Gox redeem code via Bitinstant
                    "LibertyReserve": DEPOSIT_LIBERTY_RESERVE,
                    "Paxum": DEPOSIT_PAXUM}
    feeWithdrawal = {"BTC": 0.0005,
                    "Mt.Gox code": WITHDRAWAL_MtGoxCode,
                    "Paxum": WITHDRAWAL_PAXUM}
    feeTransaction = 0.006  #0.6 %
    feeDepositDiffCurrency = 0.0025  #0.25 %
    limitsFunds = 10000  #$
    baseUrl = "https://mtgox.com/api/0/data/getDepth.php"
class mtgoxAUD(Mtgox):
    def __init__(self):
        self.asks = []
        self.bids = []
        self.currency = "?Currency=AUD"
        jsonGetBidAskFields(self)
        convertToBASE_CURRENCY(self, "AUD")
class mtgoxCAD(Mtgox):
    def __init__(self):
        self.asks = []
        self.bids = []
        self.currency = "?Currency=CAD"
        jsonGetBidAskFields(self)
        convertToBASE_CURRENCY(self, "CAD")
class mtgoxCHF(Mtgox):
    def __init__(self):
        self.asks = []
        self.bids = []
        self.currency = "?Currency=CHF"
        jsonGetBidAskFields(self)
        convertToBASE_CURRENCY(self, "CHF")
class mtgoxCNY(Mtgox):
    def __init__(self):
        self.asks = []
        self.bids = []
        self.currency = "?Currency=CNY"
        jsonGetBidAskFields(self)
        convertToBASE_CURRENCY(self, "CNY")
class mtgoxDKK(Mtgox):
    def __init__(self):
        self.asks = []
        self.bids = []
        self.currency = "?Currency=DKK"
        jsonGetBidAskFields(self)
        convertToBASE_CURRENCY(self, "DKK")
class mtgoxEUR(Mtgox):
    def __init__(self):
        self.asks = []
        self.bids = []
        self.currency = "?Currency=EUR"
        jsonGetBidAskFields(self)
        convertToBASE_CURRENCY(self, "EUR")
class mtgoxGBP(Mtgox):
    def __init__(self):
        self.asks = []
        self.bids = []
        self.currency = "?Currency=GBP"
        jsonGetBidAskFields(self)
        convertToBASE_CURRENCY(self, "GBP")
class mtgoxHKD(Mtgox):
    def __init__(self):
        self.asks = []
        self.bids = []
        self.currency = "?Currency=HKD"
        jsonGetBidAskFields(self)
        convertToBASE_CURRENCY(self, "HKD")
class mtgoxJPY(Mtgox):
    def __init__(self):
        self.asks = []
        self.bids = []
        self.currency = "?Currency=JPY"
        jsonGetBidAskFields(self)
        convertToBASE_CURRENCY(self, "JPY")
class mtgoxNZD(Mtgox):
    def __init__(self):
        self.asks = []
        self.bids = []
        self.currency = "?Currency=NZD"
        jsonGetBidAskFields(self)
        convertToBASE_CURRENCY(self, "NZD")
class mtgoxPLN(Mtgox):
    def __init__(self):
        self.asks = []
        self.bids = []
        self.currency = "?Currency=PLN"
        jsonGetBidAskFields(self)
        convertToBASE_CURRENCY(self, "PLN")
class mtgoxRUB(Mtgox):
    def __init__(self):
        self.asks = []
        self.bids = []
        self.currency = "?Currency=RUB"
        jsonGetBidAskFields(self)
        convertToBASE_CURRENCY(self, "RUB")
class mtgoxUSD(Mtgox):
    def __init__(self):
        self.asks = []
        self.bids = []
        self.currency = "?Currency=USD"
        jsonGetBidAskFields(self)
        convertToBASE_CURRENCY(self, "USD")
class mtgoxSEK(Mtgox):
    def __init__(self):
        self.asks = []
        self.bids = []
        self.currency = "?Currency=SEK"
        jsonGetBidAskFields(self)
        convertToBASE_CURRENCY(self, "SEK")
class mtgoxSGD(Mtgox):
    def __init__(self):
        self.asks = []
        self.bids = []
        self.currency = "?Currency=SGD"
        jsonGetBidAskFields(self)
        convertToBASE_CURRENCY(self, "SGD")
class mtgoxTHB(Mtgox):
    def __init__(self):
        self.asks = []
        self.bids = []
        self.currency = "?Currency=THB"
        jsonGetBidAskFields(self)
        convertToBASE_CURRENCY(self, "THB")

""" DEAD!
class TradeHill:
    transferDuration = 5 #10min-1hr, number of confirmations
    feeDeposit = {"Bitinstant_MtGox":DEPOSIT_BITINSTANT,    #Mt.Gox redeem code via Bitinstant
                         "Bitinstant_LibertyReserve":DEPOSIT_LIBERTY_RESERVE,
                         "Paxum":DEPOSIT_PAXUM}
    feeWithdrawal = {"Paxum":WITHDRAWAL_PAXUM}
    feeTransaction = 0
    feeDepositDiffCurrency = 0 #%
    limitsFunds = 0 #$
    accBTCaddr = "1ASqVSG9dpCDACpRyMap7sSAXjqsLxjLbE"

    baseUrl = "https://api.tradehill.com/APIv1/"
    currencyUSD = "USD/Orderbook"
    currencyEUR = "EUR/Orderbook"
class thUSD(TradeHill):
    def __init__(self):
        self.bids = []
        self.asks = []
        jsonGetBidAskFields(self, self.currencyUSD)
        #orderbook isn't sorted
        self.bids = sorted(self.bids, key = lambda field: field[0])
        self.asks = sorted(self.asks, key = lambda field: field[0])
class thEUR(TradeHill):
    def __init__(self):
        self.bids = []
        self.asks = []
        jsonGetBidAskFields(self, self.currencyEUR)
        #orderbook isn't sorted
        self.bids = sorted(self.bids, key = lambda field: field[0])
        self.asks = sorted(self.asks, key = lambda field: field[0])

        convertToBASE_CURRENCY(self, "EUR")
 """
#https://vircurex.com/welcome/help?locale=en
#trading API: https://vircurex.com/welcome/api?locale=en
class Vicurex:
    transferDuration = 6  #number of confirmations
    feeDeposit = {"BTC": 0.0005,
                    "LibertyReserve": DEPOSIT_LIBERTY_RESERVE}
    feeWithdrawal = {"BTC": 0.01,
                    "LibertyReserve": WITHDRAWAL_LIBERTY_RESERVE}
    feeTransaction = 0.005
    feeWithdrawal = 0.01  #BTC
    feeDepositDiffCurrency = 0
    limitsFunds = 0
    accBTCaddr = "17JXELyTiq7XtJZpe8P61whwGCHMxBtWUH"
    baseUrl = "https://vircurex.com/api/orderbook.json"
class vcxEUR(Vicurex):
    def __init__(self):
        self.asks = []
        self.bids = []
        self.currency = "?base=BTC&alt=eur"
        jsonGetBidAskFields(self)
        convertToBASE_CURRENCY(self, "EUR")
class vcxUSD(Vicurex):
    def __init__(self):
        self.asks = []
        self.bids = []
        self.currency = "?base=BTC&alt=usd"
        jsonGetBidAskFields(self)
        convertToBASE_CURRENCY(self, "USD")
