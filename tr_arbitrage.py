from lib.exchanges import *
import time
import os

def clearScreen():
    os.system(['clear','cls'][os.name == 'nt'])


FEATURES = [
            #btcdeEUR,
            btceUSD,
            btcexUSD,
            virtexCAD,            
            cryptoxUSD, cryptoxAUD,            
            intrsngGBP, intrsngEUR, intrsngUSD, intrsngPLN, 
            mtgoxUSD, mtgoxEUR, mtgoxJPY, mtgoxCAD, mtgoxGBP, mtgoxPLN,
            vcxEUR, vcxUSD,
            thUSD, thEUR
            ]

#print best to worse bottom up, so that if terminal is to small, you'll still see top opportunities
def printNice(listOpportunities):
    #since we have a list of tuples, sort by "value"
    sortedList = sorted(listOpportunities, key = lambda lst: lst[4])
    
    for touple in sortedList:
        print "%s>%s: %.2f%%, %.4f @%s" %(touple[0], 
                                           touple[1], 
                                           touple[2], 
                                           touple[3],
                                           touple[5])
def getAmount(objectA, objectB):
    #find out how many bids are on the other exchange that are greater than ask on our 
    
    #fees in percent
    fees = objectA.feeTransaction + objectB.feeTransaction  
    len_asks = len(objectA.asks)
    len_bids = len(objectB.bids)
    start = 0
    
    no_buyers = -1
    remaining_coins = 0
    coins_to_buy = []
    btcs = 0
     
    for i in xrange(len_asks):  
        ask_price = objectA.asks[i][0]
        asks_coins = objectA.asks[i][1]
        
        #since the first is already < bidPrice, since we're in this if loop...
        #how many are offering more than what is the ask price on E1
        
        buyers_coins = 0
        for j in xrange(start, len_bids):
            #bidList = [[price1, amount1], ...]
            bid_price = objectB.bids[j][0]
               
            #find out if arbitrage even exists                         
            ratio = bid_price/ask_price
            if ratio > 1 + fees: 
                no_buyers += 1 
                buyers_coins += objectB.bids[j][1]
                lowest_profitable_bid = bid_price
            #if the first element isn't good, the others will also not be since the list is sorted
            else:
                break
        
        #one ask can satisfy all bids
        if buyers_coins <= asks_coins:
            coins_to_buy.append(buyers_coins)      
            break
        #our guy has not enough coins to satisfy demand, check if the next guy has appropriate price
        else:            
            coins_to_buy.append(asks_coins)
            
            #handling when nearing 0 remaining coins for a bid
            remaining_coins = objectB.bids[start][1] - asks_coins
            
            if remaining_coins == 0:
                start += 1 
            elif remaining_coins < 0:
                start += 1
                
                """
                if tail shorter than asks, we would end up in if buyers_coins <= loop
                so that we're here means that the tail(=buyers_coins) is > than our asks_coins
                so we can take this overdose since we're still guaranteed to be in the tail
                """
                coins_to_buy.append(remaining_coins)
                
    #sum up how many to buy
    for i in coins_to_buy:
        btcs += i  
            
    res_list = [btcs, lowest_profitable_bid]    
    return res_list  
                  
def checkOpportunities(initialized, listOpportunities):
        for objectA in initialized:
            priceAsk = objectA.asks[0][0]        
            for objectB in initialized:
                priceBid = objectB.bids[0][0]
                
                ratio = priceBid/priceAsk 
                #fees in percent
                fees = objectA.feeTransaction + objectB.feeTransaction                 
                #find out if arbitrage even exists
                if ratio > 1 + fees:               
                    percent = (ratio - 1) * 100 - fees
                    
                    #congrads, u found one. now check how many BC to buy:
                    results = getAmount(objectA, objectB)
                    buyAmount = results[0]
                    min_profitable_ammount = results[1] 
                    value = percent * buyAmount
                    
                    #list of tuples
                    listOpportunities.append((objectA.__class__.__name__, 
                                   objectB.__class__.__name__, 
                                   percent, 
                                   buyAmount, 
                                   value, 
                                   min_profitable_ammount))                                     
def initializeObjects(objectsList):
    try:
        for i in FEATURES:
            print i.__name__ + ' ',
            obj = i()
            
            #check if obj initialized and has min data
            lenB = len(obj.bids)
            if lenB > 1:
                objectsList.append(obj)
            else:
                sys.stderr.write("\n%s not added to initialized list" %i.__name__) 
        print
    except:
        e = sys.exc_info()[1]
        sys.stderr.write("\n<initializeObjects>: %s" % str(e))            

if __name__ == "__main__":    
    while True:       
        try:          
            #list where initialized objects will reside
            initialized = []
            listOpportunities = []
            
            start_time = time.time()
            #initialize objects, start always with empty list!
            initializeObjects(initialized)        
            end_time = time.time()
            
            #flush the terminal
            clearScreen()   
            
            #do your thing
            checkOpportunities(initialized, listOpportunities)
            printNice(listOpportunities)
            
            #API is cached to 10s   
            takenForInitialization = start_time - end_time
            time.sleep(5 - takenForInitialization)
        except:
            e = sys.exc_info()[1]
            errorFunction(e, "<EXITING><main>: ")
            sys.exit()
        
       
        
     