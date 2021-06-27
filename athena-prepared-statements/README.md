athena prepared statements
==============================

Prepared Statementsをboto3から利用する．

## 事前準備
CloudTrailログをS3に保存する．

Athenaのテーブル作成には[公式ドキュメント](https://docs.aws.amazon.com/ja_jp/athena/latest/ug/cloudtrail-logs.html)に従い，
パーティション射影を用いたテーブルを作成する．
ただし，公式ドキュメントの方法では日付でしかパーティションが作成されない．
AWSリージョンもパーティションに追加したい場合はカスタマイズする．
カスタマイズ方法は [クラスメソッドさんの記事](https://dev.classmethod.jp/articles/cloudtrail-athena-partition-projection-table/)が参考になる．
場合によってはAWSアカウントIDでもパーティションを作成してもよいかも．

上記セットアップが完了すると，以下のようなクエリでログが取得できるようになる．

```sql
SELECT *
  FROM "default"."cloudtrail_logs"
 WHERE region = 'ap-northeast-1' AND timestamp = '2021/06'
 LIMIT 10;
```

## 

## Refs
- [Querying with Prepared Statements - AWS Documentation](https://docs.aws.amazon.com/athena/latest/ug/querying-with-prepared-statements.html)
