#!/usr/bin/env python

import os
import sys
import time

import boto3
import pandas as pd

athena = boto3.client('athena')
s3 = boto3.resource('s3')

resp = athena.start_query_execution(
    QueryString = """
    EXECUTE cloudtrail
    USING 'ap-northeast-1', '2021/06';
    """,
    ResultConfiguration = {
        'OutputLocation': 's3://' + os.environ['AWS_S3_BUCKET_QUERY_RESULTS']
    }
)
execution_id = resp['QueryExecutionId']
resp = athena.get_query_execution(QueryExecutionId=execution_id)
while resp['QueryExecution']['Status']['State'] in ['RUNNING', 'QUEUED']:
    time.sleep(3)
    resp = athena.get_query_execution(QueryExecutionId=execution_id)

if resp['QueryExecution']['Status']['State'] in ['FAILED', 'CANCELLED']:
    print(resp)
    sys.exit(1)

result_key = execution_id + '.csv'
s3.meta.client.download_file(os.environ['AWS_S3_BUCKET_QUERY_RESULTS'], result_key, 'result.csv')

list = pd.read_csv('result.csv').values.tolist()
for log in list:
    print(log)
