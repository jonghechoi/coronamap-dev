from urllib.parse import urlencode, unquote, quote_plus
from datetime import datetime,timedelta
from urllib.request import urlopen
import pandas as pd
import xmltodict # 결과가 xml 형식으로 반환된다. 이것을 dict 로 바꿔주는 라이브러리다
import requests
import pymysql
import pickle
import urllib
import folium
import json
import os


def admin_districts_changer(num):
    if num == '42':
        num = '32'
    elif num == '41':
        num = '31'
    elif num == '48':
        num = '38'
    elif num == '47':
        num = '37'
    elif num == '29':
        num = '24'
    elif num == '27':
        num = '22'
    elif num == '30':
        num = '25'
    elif num == '26':
        num = '21'
    elif num == '36':
        num = '29'
    elif num == '31':
        num = '26'
    elif num == '28':
        num = '23'
    elif num == '46':
        num = '36'
    elif num == '45':
        num = '35'
    elif num == '50':
        num = '39'
    elif num == '44':
        num = '34'
    elif num == '43':
        num = '33'
    return num


def name_changer(name):
    if len(name) >= 5:
        name = name[:2]
    elif len(name) == 4:
        name = name[0] + name[2]
    else:
        name = name[:-1]
    return name 


class CoronaCheck:
    def __init__(self):
        pass

    def action(self):
        # 어제 날짜와 오늘날짜를 구하기 위해서  datetime과 timedelta를 사용
        yester = datetime.today() - timedelta(1)
        yseter =  yester.strftime("%Y%m%d")
        now_today = datetime.today().strftime("%Y%m%d")

        my_api_key = 'Wcgao4rabgjIy%2FySdMTfP%2BO9dVXqUYCAUyMenwN%2BWFsj%2BtXvR3bIrUhW%2B7lUfnn3UYxDJ4uSlIes1UmY4URRdQ%3D%3D'

        # 서비스 url 주소
        url = 'http://openapi.data.go.kr/openapi/service/rest/Covid19/getCovid19SidoInfStateJson'

        # 서비스에 필요한 파라미터 모음
        queryParams = '?' + \
        'ServiceKey=' + '{}'.format(my_api_key) + \
        '&pageNo='+ '1' + \
        '&numOfRows='+ '999' + \
        '&startCreateDt={}&endCreateDt={}'.format(yseter,now_today)

        final_url = url + queryParams


        res = urllib.request.urlopen(final_url)
        json_str = res.read().decode("utf-8")


        jsonString = json.dumps(xmltodict.parse(json_str), indent = 4, ensure_ascii=False)
        jsonString = jsonString.replace('createDt', '등록일시분초').replace('deathCnt', '사망자수').replace('defCnt', '확진자수').replace('gubun', '시도명(한글)').replace('gubunCn', '시도명(중국어)').replace('gubunEn', '시도명(영어)').replace('incDec', '전일대비증가수').replace('isolClearCnt', '격리해제수').replace('isolIngCnt', '격리중환자수').replace('localOccCnt', '지역발생수').replace('overFlowCnt', '해외유입수').replace('qurRate', '10만명당발생률').replace('seq', '게시글번호').replace('stdDay', '기준일시').replace('updateDt', '수정일시분초')

        json_object = json.loads(jsonString)


        res2 = pd.DataFrame(json_object["response"]["body"]["items"]["item"])

      
        pickle.dump(res2, open('corona19_data.pickle', 'wb'))
        corona19_data = pickle.load(open('corona19_data.pickle', 'rb'))

        now_today2 = datetime.today().strftime("%Y-%m-%d")


        # "corona19_data['등록일시분초']"의 원래 dtype는 object 이다.
        # 문자열(object)을 datetime64 타입으로 변경하면 요일부터 다양한 추가 정보를 이용할 수 있습니다.
        corona19_data['등록일시분초'] = pd.to_datetime(corona19_data['등록일시분초'], format='%Y-%m-%d %H:%M:%S', errors='raise')
        corona19_data['등록일시분초'] = corona19_data['등록일시분초'].dt.date.astype(str)


        # If no today data was updated yet, make the latest data take place in!!
        if now_today2 in corona19_data['등록일시분초'].unique():
            corona19_data2 = corona19_data[corona19_data['등록일시분초'] == now_today2]
        else:
            latest_data = max(corona19_data2['등록일시분초'].unique())
            corona19_data2 = corona19_data[corona19_data['등록일시분초'] == latest_data]

      
        corona19_data3 = corona19_data2.loc[:, ['등록일시분초', '시도명(한글)', '전일대비증가수']]

        corona19_data4 = corona19_data3[~(corona19_data3['시도명(한글)'] == '검역') & ~(corona19_data3['시도명(한글)'] =='합계')] 

        admin_districts = pd.read_excel('AdminDistricts.xlsx', sheet_name='1. 총괄표(현행)')


        ad_dis2 = admin_districts.loc[1:, '행정구역분류 총괄표(2019.10.1.기준)':'Unnamed: 2']

        ad_dis3 = ad_dis2.rename(columns=ad_dis2.iloc[0])
        ad_dis4 = ad_dis3.drop(ad_dis3.index[0])

        ad_dis5 = ad_dis4.drop_duplicates(['대분류'])

        # 결측치 제거하기. axis=0은 행, axis=1은 열
        ad_dis6 = ad_dis5.dropna(axis=0)


        ad_dis6.to_csv('ad_dis.csv', mode='w')

        ad_dis_reborn = pd.read_csv('ad_dis.csv')
        ad_dis_reborn['시도'] = ad_dis_reborn['시도'].apply(lambda x : name_changer(x))

        merge_data = pd.merge(corona19_data4, ad_dis_reborn, left_on='시도명(한글)', right_on='시도')
        final_data = merge_data[['대분류', '전일대비증가수']]

        
        final_data['전일대비증가수'] = final_data['전일대비증가수'].astype(float)
        final_data2 = final_data.sort_values(by='전일대비증가수', axis=0, ascending=False)
        final_data2.columns = ['code', 'population']
        final_data2['code'] = final_data2['code'].astype(str)
        final_data2 = final_data2.values.tolist()
        
        mysql.writeSql(final_data2)
        final_data3 = mysql.readSql()
        final_data4 = pd.DataFrame(list(final_data3))
        final_data4.columns = ['code', 'population']
        print(final_data4)

        geoJson_for_dump = json.load(open('TL_SCCO_CTPRVN_WGS84.json', 'r'), encoding='cp949')

        for i in range(17):
            geoJson_for_dump["features"][i]["properties"]["CTPRVN_CD"] = admin_districts_changer(geoJson_for_dump["features"][i]["properties"]["CTPRVN_CD"])


        with open('TL_SCCO_CTPRVN_WGS84_renewal.json', 'w') as fi:
            json.dump(geoJson_for_dump, fi)


        state_geo = 'TL_SCCO_CTPRVN_WGS84_renewal.json'
        m = folium.Map(location=[36, 127], tiles="OpenStreetMap", zoom_start=7)

        m.choropleth(
        geo_data=state_geo,
        name='choropleth',
        data=final_data4,
        columns=('code', 'population'),
        key_on='feature.properties.CTPRVN_CD',
        fill_color='YlGn',
        fill_opacity=0.8,
        line_opacity=0.9,
        legend_name='Population Rate (%)'
        )

        m.save('templates/map.html')




class MysqlDB:
    def __init__(self):
        self.host = os.environ['MYSQL_SERVICE_IP'] # mysql service clusterIP
        print(f'\n\n mysql-service-ip : {self.host} \n\n')
        self.user = 'root'
        self.password = 'dktlrtm3'
        self.dbname = 'coronamap'

        self.columns = "code, population"

    def createTable(self):
        db = pymysql.connect(host=self.host, user=self.user, password=self.password, db=self.dbname, charset="utf8")
        curs = db.cursor()       

        sql = "use coronamap"
        curs.execute(sql)

        sql = "CREATE TABLE IF NOT EXISTS coronamap(code INT, population FLOAT)"
        curs.execute(sql)

        db.commit()
        db.close()


    def writeSql(self, data):
        db = pymysql.connect(host=self.host, user=self.user, password=self.password, db=self.dbname, charset="utf8")
        curs = db.cursor()
        
        for val in data:
            listTostr = f'{val[0]}, {val[1]}'
            sql = "INSERT INTO coronamap ({}) VALUES ({})".format(self.columns, listTostr) 
            curs.execute(sql)
        
        db.commit()
        db.close()

    def readSql(self):
        db = pymysql.connect(host=self.host, user=self.user, password=self.password, db=self.dbname, charset="utf8")
        curs = db.cursor()

        sql = "select * from coronamap"
        curs.execute(sql)

        rows = curs.fetchall()
        db.close()

        return rows




if __name__ == '__main__':
    corona_check = CoronaCheck()
    mysql = MysqlDB()
    mysql.createTable()
    corona_check.action()
    
    # mysql.writeSql()
    # mysql.readSql()