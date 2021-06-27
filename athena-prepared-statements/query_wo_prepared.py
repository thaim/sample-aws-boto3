#!/usr/bin/env python

import os
import time

import boto3
import pandas as pd

athena = boto3.client('athena')
s3 = boto3.resource('s3')

resp = athena.start_query_execution(
    QueryString = """
    SELECT *
    FROM \"cloudtrail_logs\"
    WHERE region = 'ap-northeast-1' AND timestamp = '2021/06'
    LIMIT 10;
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

print(resp)

result_key = execution_id + '.csv'
s3.meta.client.download_file(os.environ['AWS_S3_BUCKET_QUERY_RESULTS'], result_key, 'result.csv')

list = pd.read_csv('result.csv').values.tolist()
print(list)
