import json
import os
import uvicorn
import sys
import time
import jaydebeapi
import pymysql
import prestodb
import requests

from datetime import datetime, timedelta
from pymongo import MongoClient
#from utils import CloudObjectStorageReader, CustomWatsonX, create_sparse_vector_query_with_model, create_sparse_vector_query_with_model_and_filter
from dotenv import load_dotenv

# Fast API
from fastapi import FastAPI, Security, HTTPException
from fastapi.security.api_key import APIKeyHeader
from starlette.status import HTTP_403_FORBIDDEN
from fastapi.middleware.cors import CORSMiddleware

# ElasticSearch
#from elasticsearch import Elasticsearch, AsyncElasticsearch


# wx.ai
from ibm_watson_machine_learning.foundation_models import Model
from ibm_watson_machine_learning.metanames import GenTextParamsMetaNames as GenParams
from ibm_watson_machine_learning.foundation_models.prompts import PromptTemplateManager
from ibm_watson_machine_learning.foundation_models.utils.enums import PromptTemplateFormats
import pandas as pd


# Custom type classes
from customTypes.texttosqlRequest import texttosqlRequest
from customTypes.texttosqlResponse import texttosqlResponse

app = FastAPI()

# Set up CORS
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

load_dotenv()
# RAG APP Security
API_KEY_NAME = "APP-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

# Token to IBM Cloud
ibm_cloud_api_key = os.environ.get("IBM_CLOUD_API_KEY")
project_id = os.environ.get("WX_PROJECT_ID")
wx_deployment_url = os.environ.get("WX_DEPLOYMENT_URL")
wx_json_deployment_url = os.environ.get("WX_JSON_DEPLOYMENT_URL")

print("token")
token_updated_at = None
token = None
headers = None

def get_auth_token(api_key):
    auth_url = "https://iam.cloud.ibm.com/identity/token"
    
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json"
    }
    
    data = {
        "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
        "apikey": api_key
    }
    response = requests.post(auth_url, headers=headers, data=data, verify=False)
    
    if response.status_code == 200:
        return response.json().get("access_token")
    else:
        raise Exception("Failed to get authentication token")

def update_token_if_needed(api_key):
    global token, token_updated_at, headers
    if token is None or datetime.now() - token_updated_at > timedelta(minutes=20):
        print(f'updating token')
        token =  get_auth_token(api_key)
        token_updated_at = datetime.now()
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {token}"
        }

#iam_token = get_auth_token(os.getenv("IBM_CLOUD_API_KEY", None))

# wxd creds
# wxd_creds = {
#     "username": os.environ.get("WXD_USERNAME"),
#     "password": os.environ.get("WXD_PASSWORD"),
#     "wxdurl": os.environ.get("WXD_URL")
# }

# wd_creds = {
#     "apikey": os.environ.get("WD_API_KEY"),
#     "wd_url": os.environ.get("WD_URL")
# }

# WML Creds
wml_credentials = {
    "url": os.environ.get("WX_URL"),
    "apikey": os.environ.get("IBM_CLOUD_API_KEY")
}

# COS Creds
# cos_creds = {
#     "cosIBMApiKeyId": os.environ.get("COS_IBM_CLOUD_API_KEY"),
#     "cosServiceInstanceId": os.environ.get("COS_INSTANCE_ID"),
#     "cosEndpointURL": os.environ.get("COS_ENDPOINT_URL")
# }

# DB2 Creds
db2_creds = {
    "db_hostname": os.environ.get("DB2_HOSTNAME"),
    "db_port": os.environ.get("DB2_PORT"),
    "db_user": os.environ.get("DB2_USERNAME"),
    "db_password": os.environ.get("DB2_PASSWORD"),
    "db_database": os.environ.get("DB2_DATABASE"),
    "db_schema": os.environ.get("DB2_SCHEMA")
}

mysql_creds = {
    "db_hostname": os.environ.get("MYSQL_HOSTNAME"),
    "db_port": os.environ.get("MYSQL_PORT"),
    "db_user": os.environ.get("MYSQL_USERNAME"),
    "db_password": os.environ.get("MYSQL_PASSWORD"),
    "db_database": os.environ.get("MYSQL_DATABASE"),
    "tls_location": os.environ.get("MYSQL_TLS_LOCATION")
}

mdb_creds = {
    "db_hostname": os.environ.get("MDB_HOSTNAME"),
    "db_port": os.environ.get("MDB_PORT"),
    "db_user": os.environ.get("MDB_USERNAME"),
    "db_password": os.environ.get("MDB_PASSWORD"),
    "db_database": os.environ.get("MDB_DATABASE"),
    "db_schema": os.environ.get("MDB_SCHEMA"),
    "tls_location": os.environ.get("MDB_TLS_LOCATION")
}

presto_creds = {
    "db_hostname": os.environ.get("PRESTO_HOSTNAME"),
    "db_port": os.environ.get("PRESTO_PORT"),
    "db_user": os.environ.get("PRESTO_USERNAME"),
    "db_password": os.environ.get("PRESTO_PASSWORD"),
    "db_catalog": os.environ.get("PRESTO_CATALOG"),
    "db_schema": os.environ.get("PRESTO_SCHEMA"),
    "tls_location": os.environ.get("PRESTO_TLS_LOCATION")
}

# Create a watsonx client cache for faster calls.
custom_watsonx_cache = {}

# Basic security for accessing the App
async def get_api_key(api_key_header: str = Security(api_key_header)):
    if api_key_header == os.environ.get("APP_API_KEY"):
        return api_key_header
    else:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN, detail="Could not validate APP credentials. Please check your ENV."
        )

@app.get("/")
def index():
    return {"Hello": "World"}

'''
@app.post("/classify")
async def classify(request: classifyRequest, api_key: str = Security(get_api_key)):

    print(request.question)
    query = request.question
    llmparams = request.classifyllm_params
    watsonxSQLResponse = watsonx (query,"promptClassify", "", llmparams)
   
    classify = [{'Classify': watsonxSQLResponse}]
    classification = ""

    if "sqlgen" in watsonxSQLResponse:
        classification = "sqlgen"
    else:
        classification = "unknown"
        print(classify)

    print(watsonxSQLResponse)

    return classifyResponse(response=classification)
'''
@app.post("/texttosql")
async def texttosql(request: texttosqlRequest, api_key: str = Security(get_api_key)):

    print("Request: " + request.question)
    nl_query = request.question
    dbtype = request.dbtype
    llm_params = request.llm_params

    sql_payload = {"parameters": {"prompt_variables": {"input" : nl_query}}}
    watsonxSQLResponse = watsonx (nl_query,wx_deployment_url, sql_payload)

    response_from_watsonx = watsonxSQLResponse.replace('\n','').replace('Output:','').replace(';','')
    split_string = response_from_watsonx.split(":")
    query_type = split_string[0]
    sql_query_from_watsonx = split_string[1]

    nlResponse = {}
    try:
      nlResponse['nl_question'] = nl_query
      nlResponse['sql_query'] = sql_query_from_watsonx
      nlResponse['query_type'] = query_type
      output_json_dict = await queryexec(sql_query_from_watsonx, dbtype)
      
      
    except Exception as e:
      nlResponse['error'] = str(e)
    else:
      if query_type == "CONFIGUDF":
        process_answer = "[" + output_json_dict.get("answer").replace("}{", "},{") + "]"
        json_payload = {"parameters": {"prompt_variables": {"json" : process_answer,"input" : nl_query}}}
         
        answer = watsonxSQLResponse = watsonx (nl_query,wx_json_deployment_url, json_payload)
        nlResponse['result'] = answer.replace('Output:','').replace(';','')
      else:
        nlResponse['result'] = "[" + output_json_dict.get("answer").replace("}{", "},{") + "]"
      # add logic to determine when to render, for now always pass along to Sequifi to render
      nlResponse['render'] = "True"


    return texttosqlResponse(response=nlResponse)

# Caching database connection
db_connections = {}
async def get_db_connection(dbtype):
    print("in connections")
    if dbtype in db_connections:
        return db_connections[dbtype]

    if dbtype == "DB2":
        SQL_DATABASE_URL = "jdbc:db2://" + str(db2_creds["db_hostname"]) + ":" + str(db2_creds["db_port"]) + "/" + str(db2_creds["db_database"]) + ":currentSchema=" + str(db2_creds["db_schema"]) + ";user=" + str(db2_creds["db_user"]) + ";password=" + str(db2_creds["db_password"]) + ";sslConnection=true;"
        print("SQL created " + SQL_DATABASE_URL)
        conn = jaydebeapi.connect("com.ibm.db2.jcc.DB2Driver", SQL_DATABASE_URL, None, "db2jcc4.jar")
    
    elif dbtype == "MYSQL":

        conn = pymysql.connect(
                        host=str(mysql_creds["db_hostname"]),
                        port=int(mysql_creds["db_port"]),
                        database=str(mysql_creds["db_database"]),
                        user=str(mysql_creds["db_user"]),
                        passwd=str(mysql_creds["db_password"]),
                        ssl={'ca': None})
    
    elif dbtype == "MONGODB":
        tls_ca_file =  str(mdb_creds["tls_location"])
        username = str(mdb_creds["db_user"])
        password = str(mdb_creds["db_password"]) 
        host = str(mdb_creds["db_hostname"])
        port = str(mdb_creds["db_port"])  # default MongoDB port
        conn =  MongoClient(f'mongodb://{username}:{password}@{host}:{port}',tls=True,tlsCAFile=tls_ca_file)
    elif dbtype == "PRESTO":
        #print("in presto" + str(presto_creds["db_password"]) + " " + str(presto_creds["db_user"]) + " " + str(presto_creds["db_hostname"]))
        with prestodb.dbapi.connect(
            host=str(presto_creds["db_hostname"]),
            port=str(presto_creds["db_port"]),
            user=str(presto_creds["db_user"]),
            catalog=str(presto_creds["db_catalog"]),
            schema=str(presto_creds["db_schema"]),
            http_scheme='https',
            auth=prestodb.auth.BasicAuthentication(str(presto_creds["db_user"]), str(presto_creds["db_password"]))
            )as conn:
             conn._http_session.verify = str(presto_creds["tls_location"])
    else:
        raise ValueError("Unsupported database type")

    db_connections[dbtype] = conn
    return conn

@app.route("/queryexec", methods=['POST'])
async def queryexec(query, dbtype):
       
    conn = await get_db_connection(dbtype)  
    print ("SQL DB Connection: " + str(conn))
  
    cur = conn.cursor()
    
    cur.execute(query)
    rows = cur.fetchall()
    op=""

    for row in rows:
        br="" 
        for i,col in enumerate(row):
            key=cur.description[i][0]
            br += "{}:{},".format(key,col)
        br = br[:-1]
        op += "{" + br + "}"

    nl=""
    history=""
    image=""
    response = dict(answer=op,query=query,nl=nl,history=history,image=image)
    return response

def get_latest_prompt_template(promptType):
    prompt_mgr = PromptTemplateManager(
        credentials={
            "apikey": os.environ.get("IBM_CLOUD_API_KEY"),
            "url": os.environ.get("WX_URL"),
        },
        space_id=os.environ.get("WX_SPACE_ID")
    )
    
    df_prompts = prompt_mgr.list()

    df_prompts = df_prompts.assign(
            NAME=df_prompts['NAME'].astype(str),
            LAST_MODIFIED=pd.to_datetime(df_prompts['LAST MODIFIED'])
        )

    filtered_df = df_prompts[df_prompts['NAME'] == promptType]

    if filtered_df.empty:
        raise ValueError(f"Prompt file does not exist for NAME = {promptType}")

    # Find the latest record and prompt id based on 'LAST MODIFIED'
    latest_index = filtered_df['LAST MODIFIED'].idxmax()
    latest_record = filtered_df.loc[latest_index]

    latest_prompt_id = latest_record['ID']

    # Load the prompt template using the latest ID and format type as string
    loaded_prompt_template_string = prompt_mgr.load_prompt(latest_prompt_id, PromptTemplateFormats.STRING, prompt_variables={"input": "test"})
    print(loaded_prompt_template_string)
    return loaded_prompt_template_string

#@app.post("/watsonx")
def watsonx(input, promptType, payload):
    '''
    generate_params = {
        GenParams.MIN_NEW_TOKENS: llm_params.parameters.min_new_tokens,
        GenParams.MAX_NEW_TOKENS: llm_params.parameters.max_new_tokens,
        GenParams.DECODING_METHOD: llm_params.parameters.decoding_method,
        GenParams.REPETITION_PENALTY: llm_params.parameters.repetition_penalty,
        GenParams.TEMPERATURE: llm_params.parameters.temperature,
        GenParams.STOP_SEQUENCES: llm_params.parameters.stop_sequences,
        GenParams.TOP_K: llm_params.parameters.top_k,
    }
    '''
    #iam_token = get_auth_token(os.getenv("IBM_CLOUD_API_KEY", None))
    
    update_token_if_needed(os.getenv("IBM_CLOUD_API_KEY", None))

    response = requests.post(promptType, headers=headers, json=payload, verify=False).json()
    print("RESPONSE : " + str(response))
    message = response['results'][0]['generated_text']
    print(" message: " + str(message))
    return message
if __name__ == '__main__':
    if 'uvicorn' not in sys.argv[0]:
        uvicorn.run("app:app", host='0.0.0.0', port=4050, reload=True)
