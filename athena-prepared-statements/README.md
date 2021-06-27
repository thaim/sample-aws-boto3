athena prepared statements
==============================

Prepared Statementsをboto3から利用する。

## 事前準備
CloudTrailログをS3に保存する。
CloudTrailログについては省略。詳細は[CloudTrailに関する公式ドキュメント](https://docs.aws.amazon.com/ja_jp/awscloudtrail/latest/userguide/cloudtrail-create-and-update-a-trail.html)を参照。

Athenaエンジンをバージョン2にアップグレードする。
prepared statement は Athena エンジンバージョン2からサポートされた機能なので
バージョン2の利用が必須。
明示的にバージョン1を利用することを選択していない限り自動的にバージョン2にアップデート済かも。
詳細はAthenaエンジンバージョン2に関する[公式ドキュメント](https://docs.aws.amazon.com/athena/latest/ug/engine-versions.html)を参照。

Athenaのテーブル作成には[公式ドキュメント](https://docs.aws.amazon.com/ja_jp/athena/latest/ug/cloudtrail-logs.html)に従い、
パーティション射影を用いたテーブルを作成する。
ただし、公式ドキュメントの方法では日付でしかパーティションが作成されない。
また、クエリの際に日々まで指定する必要が出てくる。
AWSリージョンもパーティションに追加したい場合やパーティションには月単位を指定したい場合はカスタマイズする。
カスタマイズ方法は [クラスメソッドさんの記事](https://dev.classmethod.jp/articles/cloudtrail-athena-partition-projection-table/)が参考になる。
場合によってはAWSアカウントIDでもパーティションを作成してもよいかも。
以上を踏まえて以下のようなテーブルを作成した。

```sql
CREATE EXTERNAL TABLE cloudtrail_logs(
         eventVersion STRING,
         userIdentity STRUCT< type: STRING,
         principalId: STRING,
         arn: STRING,
         accountId: STRING,
         invokedBy: STRING,
         accessKeyId: STRING,
         userName: STRING,
         sessionContext: STRUCT< attributes: STRUCT< mfaAuthenticated: STRING,
         creationDate: STRING>,
         sessionIssuer: STRUCT< type: STRING,
         principalId: STRING,
         arn: STRING,
         accountId: STRING,
         userName: STRING>>>,
         eventTime STRING,
         eventSource STRING,
         eventName STRING,
         awsRegion STRING,
         sourceIpAddress STRING,
         userAgent STRING,
         errorCode STRING,
         errorMessage STRING,
         requestParameters STRING,
         responseElements STRING,
         additionalEventData STRING,
         requestId STRING,
         eventId STRING,
         readOnly STRING,
         resources ARRAY<STRUCT< arn: STRING,
         accountId: STRING,
         type: STRING>>,
         eventType STRING,
         apiVersion STRING,
         recipientAccountId STRING,
         serviceEventDetails STRING,
         sharedEventID STRING,
         vpcEndpointId STRING
) PARTITIONED BY (
        `region` string,
         `timestamp` string
)
ROW FORMAT SERDE 'com.amazon.emr.hive.serde.CloudTrailSerde'
STORED AS INPUTFORMAT 'com.amazon.emr.cloudtrail.CloudTrailInputFormat'
OUTPUTFORMAT 'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat'
LOCATION 's3://BUCKET_NAME/AWSLogs/AWS_ACCOUNT_ID/CloudTrail/'
TBLPROPERTIES (
  'projection.enabled'='true',
  'projection.timestamp.format'='yyyy/MM',
  'projection.timestamp.interval'='1',
  'projection.timestamp.interval.unit'='MONTHS',
  'projection.timestamp.range'='2018/01,NOW',
  'projection.timestamp.type'='date',
  'projection.region.type' = 'enum',
  'projection.region.values'='us-east-1,us-east-2,us-west-1,us-west-2,af-south-1,ap-east-1,ap-south-1,ap-northeast-2,ap-southeast-1,ap-southeast-2,ap-northeast-1,ca-central-1,eu-central-1,eu-west-1,eu-west-2,eu-south-1,eu-west-3,eu-north-1,me-south-1,sa-east-1',
  'storage.location.template'='s3://BUCKET_NAME/AWSLogs/AWS_ACCOUNT_ID/CloudTrail/${region}/${timestamp}'
)
```

上記セットアップが完了すると、以下のようなクエリでログが取得できるようになる。

```sql
SELECT *
  FROM "default"."cloudtrail_logs"
 WHERE region = 'ap-northeast-1' AND timestamp = '2021/06'
 LIMIT 10;
```

## 環境構築
poetryとしてまとめているので、
`poetry install && poetry shell` で環境構築は完了。
`env.sh` にクエリ結果を保存するバケット名を記載して
`source env.sh` で環境変数でバケット名をスクリプトに渡せるようにする。


## prepared statementsなしの実行
`python query_wo_prepared.py` で実行する。
正常にクエリを実行できていれば、実行結果をS3からダウンロードして結果を表示できる。
今回やりたいことは、これを prepared statementを用いて実行すること。


## prepared statementsを用いた実行
boto3を用いた prepared statements の作成・実行方法は大きく2つの方法がある。

### start_query_executionで作成する
`PREPARE` 句を利用することで通常のクエリと同様にprepared statementsを作成・更新することができる。

通常のクエリと異なるのは、実行結果がS3に保存されるのではなく、直接レスポンスとして返ること。
実行結果が S3 に `<execution_id>.txt` として保存されるが、試した限り内容は常に空だった。
prepared statementsの作成に失敗する場合はエラーメッセージが保存されるかもしれないが、
エラーになるケースが思い付かなかった。

boto3から呼び出す実装サンプルは `python_create_prepared.py --command` で実行する。
prepared statement の作成に成功すると `create or update prepared statement: ` と表示している。
(実際にはS3に生成された実行結果のファイルを表示しているが内容が空なので何も出力されない)。
実際に作成された prepared statement は以下の通り。
デフォルトで Description が設定される。

```
$ aws athena get-prepared-statement --work-group primary --statement-name cloudtrail
{
    "PreparedStatement": {
        "StatementName": "cloudtrail",
        "QueryStatement": "SELECT *\nFROM\n  cloudtrail_logs\nWHERE ((region = ?) AND (timestamp = ?))\nLIMIT 10\n",
        "WorkGroupName": "primary",
        "Description": "Created through SQL command.",
        "LastModifiedTime": "2021-06-27T22:38:30.314000+09:00"
    }
}
```

### create_prepared_statementで作成する
prepared statementを作成する専用のAPIが提供されているのでこれを用いて作成する。

通常のクエリとは異なり、クエリの実行を待つ必要がなくなるため `get_query_execution` で
実行したクエリの結果を確認するといった作業が不要になる。
prepared statementに不正がある場合は `create_prepared_statement` の実行時にエラーになってくれる。

一方で、prepared statementの作成と更新でAPIが異なることが面倒という課題がある。
同一名称のprepared statementが既に存在する場合、 `create_prepared_statement` は失敗する。
また、同一名称のprepared statementが存在しない場合、 `update_prepared_statement` は失敗する。

```
(create_prepared_statementでエラー)
botocore.errorfactory.InvalidRequestException: An error occurred (InvalidRequestException) when calling the CreatePreparedStatement operation: Prepared Statement cloudtrail already exists in WorkGroup primary

(update_prepared_statementでエラー)
botocore.errorfactory.ResourceNotFoundException: An error occurred (ResourceNotFoundException) when calling the UpdatePreparedStatement operation: Prepared Statement cloudtrail does not exist in WorkGroup primary 
```

対策としては対象のprepared statementが存在するか確認した上で create or updateを使い分ける必要がある。
ただし、 `get_prepared statement` は対象の prepared statement が存在しなければ例外になる。
このため、エラーハンドリングが必要で少し面倒。

boto3から呼び出す実装サンプルは `python_create_prepared.py --api` で実行する。
いずれも API 自体はレスポンスを返さないので

```
$ python query_create_prepared.py --api
create prepared statement: {'ResponseMetadata': {'RequestId': 'f0f454b5-10ee-4832-99be-20b41daa059c', 'HTTPStatusCode': 200, 'HTTPHeaders': {'content-type': 'application/x-amz-json-1.1', 'date': 'Sun, 27 Jun 2021 13:47:10 GMT', 'x-amzn-requestid': 'f0f454b5-10ee-4832-99be-20b41daa059c', 'content-length': '2', 'connection': 'keep-alive'}, 'RetryAttempts': 0}}

$ python query_create_prepared.py --api
update prepared statement: {'ResponseMetadata': {'RequestId': 'bddfd923-197e-4285-b79c-c30572d6fa3a', 'HTTPStatusCode': 200, 'HTTPHeaders': {'content-type': 'application/x-amz-json-1.1', 'date': 'Sun, 27 Jun 2021 13:47:15 GMT', 'x-amzn-requestid': 'bddfd923-197e-4285-b79c-c30572d6fa3a', 'content-length': '2', 'connection': 'keep-alive'}, 'RetryAttempts': 0}}
```

### prepared_statementsを実行する
`python query_w_prepared.py` で実行する。
基本的なクエリの流れは prepared statement なしの場合と同じで、
実際に投げるクエリが異なるだけ。


## その他
### マネジメントコンソール上でのprepared statementの確認
マネジメントコンソール上で作成したprepared statementを確認しようとしたが，
作成済のprepared statementを表示するようなタブ等は存在しなかった．

クエリで操作できるのは作成(prepare)，実行(execute)，削除(deallocate prepare)だけなので
おそらくマネジメントコンソール上で確認することはできない．

作成済のprepared statementを確認するには，aws cliやboto3を利用する必要がある．
aws cliを利用する場合は `list-prepared-statements` や `get-prepared-statement` を利用する．

```
$ aws athena list-prepared-statements --work-group primary
{
    "PreparedStatements": [
        {
            "StatementName": "cloudtrail",
            "LastModifiedTime": "2021-06-27T18:37:53.353000+09:00"
        }
    ]
}

$ aws athena get-prepared-statement --work-group primary --statement-name cloudtrail
{
    "PreparedStatement": {
        "StatementName": "cloudtrail",
        "QueryStatement": "SELECT *\nFROM\n  cloudtrail_log\nWHERE ((region = ?) AND (timestamp = ?))\nLIMIT 10\n",
        "WorkGroupName": "primary",
        "LastModifiedTime": "2021-06-27T18:37:53.353000+09:00"
    }
}
```

boto3を利用する場合は `list_prepared_statements` や `get_prepared_statement` を利用する．

## Refs
* [Querying with Prepared Statements - AWS Documentation](https://docs.aws.amazon.com/athena/latest/ug/querying-with-prepared-statements.html)
* [Athena - Boto3 Documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/athena.html)
