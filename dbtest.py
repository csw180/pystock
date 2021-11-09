import pymysql

connection = pymysql.connect(host='localhost', port=3306, db='Investar', \
    user='root', passwd ='', autocommit=True)

cursor = connection.cursor()
cursor.execute('select version()')
result = cursor.fetchone();

print('mysql test: {}'.format(result))

connection.close()