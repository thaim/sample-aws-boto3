#!/usr/bin/env python

import os
import sys
import time

import boto3

athena = boto3.client('athena')
s3 = boto3.resource('s3')

def create_with_command():
    resp = athena.start_query_execution(
        QueryString = """
        PREPARE cloudtrail FROM
        SELECT *
        FROM \"cloudtrail_logs\"
        WHERE region = ? AND timestamp = ?
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

    if resp['QueryExecution']['Status']['State'] in ['FAILED', 'CANCELLED']:
        print(resp)
        sys.exit(1)

    result_key = execution_id + '.txt'
    s3.meta.client.download_file(os.environ['AWS_S3_BUCKET_QUERY_RESULTS'], result_key, 'result.txt')

    with open('result.txt') as f:
        # expect empty
        print('create or update prepared statement: ' + f.read())

def create_with_api():
    try:
        result = athena.get_prepared_statement(
            StatementName = "cloudtrail",
            WorkGroup = "primary"
        )
        # print('prepared statement exist: ' + str(result))
    except athena.exceptions.ResourceNotFoundException as e:
        # print('prepared statement does not exist: ' + str(e))
        result = None
    except Exception as e:
        print(e)
        sys.exit(1)

    if result is None:
        resp = athena.create_prepared_statement(
            StatementName = "cloudtrail",
            WorkGroup = "primary",
            QueryStatement = """
            SELECT *
            FROM \"cloudtrail_logs\"
            WHERE region = ? AND timestamp = ?
            LIMIT 10;
            """
        )
        print('create prepared statement: ' + str(resp))
    else:
        resp = athena.update_prepared_statement(
            StatementName = "cloudtrail",
            WorkGroup = "primary",
            QueryStatement = """
            SELECT *
            FROM \"cloudtrail_logs\"
            WHERE region = ? AND timestamp = ?
            LIMIT 10;
            """
        )
        print('update prepared statement: ' + str(resp))


if __name__ == '__main__':
    if len(sys.argv) == 1 or sys.argv[1] == '--command':
        create_with_command()
    elif sys.argv[1] == '--api':
        create_with_api()
    else:
        print('unknown arguments:' + str(sys.argv))

