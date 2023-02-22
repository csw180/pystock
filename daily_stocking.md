#### Maria DB 설치 및 기본코스
```
https://mariadb.org/
https://www.mariadbtutorial.com/mariadb-basics/   
```

#### HeidiSQL 접속해서 세션과 DB 생성
> 1. HeidiSQL 실행
> 2. 세셔관리자 > 신규 > 세션이름 'romatic' 입력
> 3. romantic 우측에 root 사용자/암호 입력
> 4. DB 생성  'home'


#### company_info create script
```
CREATE TABLE IF NOT EXISTS company_info (
    code VARCHAR(20),
    name VARCHAR(40),
    market  VARCHAR(20),
    last_update VARCHAR(8),
    PRIMARY KEY (code))

```

#### daily_price create script
```
CREATE TABLE IF NOT EXISTS daily_price (
    code VARCHAR(20),
    date VARCHAR(8),
    open BIGINT(20),
    high BIGINT(20),
    low BIGINT(20),
    close BIGINT(20),
    volume BIGINT(20),
    chg   DECIMAL(20,5),
    PRIMARY KEY (code, date))
```
