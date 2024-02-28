# sudo service mariadb start

from  pykrx import stock
import pandas   as pd
from datetime import datetime
import mariadb
import time
import argparse

def get_args():
    """Get command-line arguments"""

    parser = argparse.ArgumentParser(
        description="pytrx to DB",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('basedate', metavar='basedate', help='basedate')
   
    parser.add_argument('-c', action='store_true',help='company_info')
    parser.add_argument('-p', action='store_true',help='daily price')
    parser.add_argument('-i', action='store_true',help='daily investor value')
    parser.add_argument('-all', action='store_true',help='-c, -p -i  all enabled')
    
    return parser.parse_args()

def get_connection() :
    """
    마리아DB 접속 Connection 을 획득한다.
    """
    conn = None
    try:
        conn = mariadb.connect(
            user="root",
            password="123",
            host="localhost",
            port=3306,
            database="home"
        )
    except mariadb.Error as e:
        print(f"Error connecting to MariaDB Platform: {e}")
    finally :
        return conn

def  get_tickers(base_date) :
    """
        get_market_ticker_list 로 종목리스트를 작성하여 리턴한다.
    """
    tickers=[]
    tickers_list = stock.get_market_ticker_list(base_date,market='KOSPI')
    for ticker in tickers_list :
        tickers.append((ticker,stock.get_market_ticker_name(ticker),'KOSPI'))

    tickers_list = stock.get_market_ticker_list(base_date,market='KOSDAQ')
    for ticker in tickers_list :
        tickers.append((ticker,stock.get_market_ticker_name(ticker),'KOSDAQ'))
    
    return tickers

def update_company_info(conn, tickers, base_date) :
    """
        종목테이블(company_info) 를 갱신다.
    """
    count = 0
    today = base_date
    cursor = conn.cursor()
    for  ticker in tickers :
        count += 1
        cursor.execute("REPLACE INTO company_info (code, name, market, last_update) VALUES (?,?,?,?)",(*ticker,today))
        conn.commit()
    print(f"[company_info] {len(tickers):,} upsert completed")

def get_start_date(conn) :
    """
        현재 DB에 있는 데이터를 확인하여 몇일자 내역(daily_agent, daily_price 데이터)부터 가져와야 하는지 결정한다
        테이블에 데이터가 없는경우 default 는 20220101 로 한다.
    """
    # 현재 DB에 몇일짜 데이터까지 들어 있는지 확인
    cursor = conn.cursor()
    cursor.execute("select max(date) from daily_price")
    sdate = cursor.fetchone()[0]   # empty 이면 None  fetchone 의 return 타입은 tuple
    print(f'[daily_price] The final date of table(daily_price) is {sdate}')

    # 가지고 있는 데이터가 없는 경우 시작일자는 2022/01/01 부터로 지정함
    if sdate is None :
        sdate = '20220101'
        print(f"[daily_price] you don't have any data, the start date is assumed to be {sdate}")
    
    return sdate

def update_daily_price(conn, tickers, sdate, base_date) :
    """
        일별 OHLC 데이터를 가져와서 DB 테이블을 갱신한다.
    """
    count=0
    cursor = conn.cursor()
    for  ticker in tickers :
        try : 
            time.sleep(1)
            df = stock.get_market_ohlcv(sdate, base_date, ticker[0])
        except ValueError :
            print(f"[daily_price : {sdate=} {base_date=} {ticker[0]=}] ValueError Continue...")
            continue

        if df.empty :
            continue

        df = df.dropna().reset_index()  # 데이터 중에 NaN 있음, 날짜칼럼을 인텍스칼럼-> 일반칼럼
        df["날짜"] = df["날짜"].dt.strftime("%Y%m%d")
        df = df.drop(columns='거래대금')  # 다음에 DB 재구성할때는 포함시킬 칼럼
        for sidx,srow in df.iterrows() :
            cursor.execute("REPLACE INTO daily_price (code, date, open, high, low, close,  volume, chg) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",(ticker[0],*srow))
            conn.commit()
        count += 1
        print(f"[daily_price : ticker:{ticker[0]}]  {count:,} upsert completed")

# def update_daily_agent(conn, tickers, sdate, base_date) :
#     """
#         일별 주체별매매동향 데이터를 가져와서 DB 테이블을 갱신한다.
#     """
#     count=0
#     cursor = conn.cursor()
#     for  ticker in tickers :
#         try :
#             time.sleep(1)
#             df = stock.get_market_trading_value_by_date(sdate, base_date, ticker[0], detail=True)
#         except ValueError :
#             print(f"[daily_agent :{sdate=} {base_date=} {ticker[0]=} ] ValueError Continue...")
#             continue

#         if df.empty :
#             continue    
#         df = df.dropna().reset_index()  # 데이터 중에 NaN 있음, 날짜칼럼을 인텍스칼럼-> 일반칼럼
#         df["날짜"] = df["날짜"].dt.strftime("%Y%m%d")
#         for sidx,srow in df.iterrows() :
#             cursor.execute("REPLACE INTO daily_agent (code, date, kt, bh, ts, sm, bk, ek, yk, eb, pe, fr, ef, tot) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",(ticker[0],*srow))
#             conn.commit()
#         count += 1
#         print(f"[daily_agent : ticker:{ticker[0]}]  {count:,} upsert completed")

def update_daily_agent(conn, tickers, base_date) :
    """
        일별 주체별매매동향 데이터를 가져와서 DB 테이블을 갱신한다.
    """
    count=0
    cursor = conn.cursor()
    for  ticker in tickers :
        try :
            time.sleep(1)
            df = stock.get_market_trading_value_by_investor(base_date, base_date,ticker[0]).T
            df = df[df.index.isin(["순매수"])]
            df["날짜"] = base_date
            df = df.set_index("날짜")
            df = df.drop(columns=["기관합계"])
            df = df.dropna().reset_index()  # 데이터 중에 NaN 있음, 날짜칼럼을 인텍스칼럼-> 일반칼럼
        except ValueError :
            print(f"[daily_agent :{base_date=} {ticker[0]=} ] ValueError Continue...")
            continue

        if df.empty :
            continue    
        for sidx,srow in df.iterrows() :
            cursor.execute("REPLACE INTO daily_agent (code, date, kt, bh, ts, sm, bk, ek, yk, eb, pe, fr, ef, tot) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",(ticker[0],*srow))
            conn.commit()
        count += 1
        print(f"[daily_agent : ticker:{ticker[0]}]  {count:,} upsert completed")



def main() :
    args = get_args()
    conn = get_connection()
    base_date = args.basedate
    tickers = get_tickers(base_date)

    if args.c or args.all :
        update_company_info(conn, tickers, base_date)
    
    if args.p or args.all :
        start_date = get_start_date(conn)
        update_daily_price(conn, tickers, start_date, base_date)
    
    if  args.i or args.all :
        update_daily_agent(conn, tickers, base_date)

    conn.close()


if __name__=="__main__" :
    main()