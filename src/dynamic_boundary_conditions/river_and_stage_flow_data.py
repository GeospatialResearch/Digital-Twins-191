# -*- coding: utf-8 -*-
"""
Created on Tue Nov  9 16:16:49 2021

@author: pkh35
"""
import ssl
ssl._create_default_https_context = ssl._create_unverified_context
import geopandas as gpd
from urllib.parse import urlencode
import requests as rq
import pandas as pd
import datetime 
import dateutil.relativedelta
from src.digitaltwin import setup_environment
import sys

def check_inputs(flow):
    if flow == 'Stage Flow' or flow == 'River Flow':
        return flow
    else:
        print('request_flow_data function only accepts flow as "River Flow" or "Stage Flow"')
        sys.exit()


def sites_info_to_db(engine,df_river_gauge):
    if engine.dialect.has_table(engine.connect(), "river_gauging_sites") == False:
        df_river_gauge.to_postgis("river_gauging_sites", engine, index=False, if_exists='replace')
        

def filter_gauging_sites(url, engine, flow):
    """Filter the gauging sites which have a past month data stored in it."""
    now = datetime.datetime.now()
    prev_month = now + dateutil.relativedelta.relativedelta(months=-1)
    df_river_gauge =  gpd.read_file(url)
    sites_info_to_db(engine, df_river_gauge)
    try:
        df_river_gauge['LAST_GAUGING'] = pd.to_datetime(df_river_gauge['LAST_GAUGING']).apply(lambda x: x.replace(tzinfo=None))
        df_river_gauge = df_river_gauge[(df_river_gauge['LAST_GAUGING'] > prev_month) & (df_river_gauge['LAST_GAUGING'] <= now)]
        return df_river_gauge
    except Exception as error:
        print(error, type(error))

def request_flow_data(url_river, SiteNo, Flow, Period = '1_Month'):
  """Extract last 1 month data from each site"""
  river_df = pd.DataFrame() 
  json_dict = {'SiteNo':SiteNo , 'Period': Period, 'StageFlow': Flow}
  base_url = url_river.split('?',1)[0]
  url = base_url +'?'+ urlencode(json_dict)
  url = str.replace(url, '+', '%20')
  response =  rq.get(url)
  try:
    df = pd.DataFrame(response.json()['data']['item'])
    river_df = river_df.append(df, ignore_index=True)
    return river_df
  except Exception as error:
      print(error, type(error))
      return None

        
def flow_data_to_db(engine,gauging_sites,url_river,flow):
    flow = check_inputs(flow)
    df_river_gauge = filter_gauging_sites(gauging_sites, engine, flow) #pass url to the defined function
    #reading all the site numbers from Environment Canterbury's Gaugings Database
    flow_df = pd.DataFrame()
    for i in df_river_gauge['SITENUMBER']:
        flow_df = flow_df.append(request_flow_data(url_river, i, flow )) #change the values as per the requirements
    if flow == 'Stage Flow':
        table_name = 'stageflow'
    elif flow == 'River Flow':
        table_name = 'riverflow'
    flow_df.to_sql(table_name, engine, index=False, if_exists='append')
    
    # convert text column to timestamp
    query = 'ALTER TABLE public.%(table_name)s ADD COLUMN create_time_holder TIMESTAMP without time zone NULL;\
        UPDATE public.%(table_name)s SET create_time_holder = "DateTime"::TIMESTAMP;\
        ALTER TABLE public.%(table_name)s ALTER COLUMN "DateTime" TYPE TIMESTAMP without time zone USING create_time_holder;\
        ALTER TABLE public.%(table_name)s DROP COLUMN create_time_holder;\
        ALTER TABLE public.%(table_name)s ALTER COLUMN "Site_no" TYPE bigint USING ("Site_no"::bigint)'
    engine.execute(query % ({'table_name': table_name}))
    # delete duplicate rows from the newly created tables if exists
    engine.execute('DELETE FROM public.%(table_name)s WHERE  ctid NOT IN (SELECT\
                    min(ctid) FROM public.riverflow GROUP BY "Site_no","DateTime")' % ({'table_name': table_name}) )        
  
def flow_data_from_db(polygon, start_time, end_time, flow, engine):
    query = 'select * from public.riverflow e,public.river_gauging_sites f\
        where "DateTime" >="2021-10-15 16:00:00" and e."Site_no"=f."SITENUMBER"\
            and ST_Intersects(geometry, ST_GeomFromText({}, 2193))'
    output_data = pd.read_sql_query(query.format(polygon), engine)
    return output_data

if __name__ == '__main__':  
    engine = setup_environment.get_database()
    #Gauging sites url 
    gauging_sites = 'https://opendata.arcgis.com/datasets/1591f4b1fc03410eb7b76cde0cf1ad85_4.geojson' #river
  
    #river/stage flow data url
    url_river = 'http://data.ecan.govt.nz/data/79/Water/River%20stage%20flow%20data%20for%20individual%20site/JSON?SiteNo=63101&Period=1_Month&StageFlow=River%20Flow'
 
    # set the value as 'River Flow' or 'Stage Flow' as per the requirements   
    flow = 'Stage Flow'
    flow_data_to_db(engine, gauging_sites, url_river, flow)

    

    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    