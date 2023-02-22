# sudo service mariadb start

from  pykrx import stock
import pandas   as pd
from datetime import datetime
import mariadb

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

cursor = conn.cursor()

tickers=[]
tickers_list = stock.get_market_ticker_list(market='KOSPI')
for ticker in tickers_list :
    tickers.append((ticker,stock.get_market_ticker_name(ticker),'KOSPI'))

tickers_list = stock.get_market_ticker_list(market='KOSDAQ')
for ticker in tickers_list :
    tickers.append((ticker,stock.get_market_ticker_name(ticker),'KOSDAQ'))

count = 0
today = datetime.today().strftime('%Y%m%d')
for  ticker in tickers :
  count += 1
  cursor.execute("REPLACE INTO company_info (code, name, market, last_update) VALUES (?,?,?,?)",(*ticker,today))
  conn.commit()

cursor.execute("select max(date) from daily_price")
sdate = cursor.fetchone()[0]   # empty 이면 None  fetchone 의 return 타입은 tuple
print(f'{sdate=}')

if sdate is None :
	sdate = '20220101'

count=0
for  ticker in tickers :
    df = stock.get_market_ohlcv('20230201', "20230217", ticker[0])
    if df.empty :
        continue
    df = df.dropna().reset_index()  # 데이터 중에 NaN 있음, 날짜칼럼을 인텍스칼럼-> 일반칼럼
    df["날짜"] = df["날짜"].dt.strftime("%Y%m%d")
    df = df.drop(columns='거래대금')  # 다음에 DB 재구성할때는 포함시킬 칼럼
    for sidx,srow in df.iterrows() :
        cursor.execute("REPLACE INTO daily_price (code, date, open, high, low, close,  volume, chg) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",(ticker[0],*srow))
        conn.commit()
    count += 1
    print(f"[daily_price:{ticker[0]}]  {count:,} upsert completed")

conn.close()
# [daily_price:28513K]  154 upsert completed
# [daily_price:017670]  155 upsert completed