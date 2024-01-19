data "aws_kms_alias" "ebs" {
  name = "alias/aws/ebs"
}

## EBSを作成するために必要なIAMロール

resource "aws_iam_role" "ecs_infrastructure" {
  name               = "sample-ecs-infrastructure-role"
  assume_role_policy = data.aws_iam_policy_document.assume_ecs.json

  managed_policy_arns = [
    "arn:aws:iam::aws:policy/service-role/AmazonECSInfrastructureRolePolicyForVolumes",
  ]
}

data "aws_iam_policy_document" "assume_ecs" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ecs.amazonaws.com"]
    }
  }
}

## ECSタスクを作成するために必要なIAMロール

resource "aws_iam_role" "ecs_task" {
  name               = "sample-ecs-task-role"
  assume_role_policy = data.aws_iam_policy_document.assume_ecs_task.json

  managed_policy_arns = [
    "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy",
  ]
}

data "aws_iam_policy_document" "assume_ecs_task" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

## 今回の対象外

data "aws_subnet" "public" {
  id = "subnet-0573061dd09dba117"
}
