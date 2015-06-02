from lib.exchanges import *


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
    feeDeposit = {}
    feeWithdrawal = {}
    feeTransaction = 0  #0.6 %
    feeDepositDiffCurrency = 0  #0.25 %
    limitsFunds = 1000  #$
    baseUrl = "https://bitcoin-central.net/order_book"
class bcEUR(BitcoinCentral):
    def __init__(self):
        self.asks = []
        self.bids = []
        self.currency = ""
        getBCHTML(self)
        convertToBASE_CURRENCY(self, "EUR")


if __name__ == '__main__':
    obj = bcEUR()

    print "bids: ", obj.bids
    print "\nasks: ", obj.asks
    print obj.__class__.__name__
