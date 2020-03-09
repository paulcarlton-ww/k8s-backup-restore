data "archive_file" "lambda-zipper" {
  type        = "zip"
  source_file = "${path.module}/lambda_function.py"
  output_path = "${path.module}/lambda_function.zip"
}

resource "aws_iam_role" "hsbc-dsn-switch-dr-assumerole" {
  name        = "${var.name}"
  description = "Role for  Canopy Lambda Function"

  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Effect": "Allow",
      "Sid": ""
    }
  ]
}
EOF
}

resource "aws_iam_role_policy" "hsbc-dsn-switch-dr-policy" {
  name = "${var.name}-role-policy"
  role = "${aws_iam_role.hsbc-dsn-switch-dr-assumerole.id}"

  policy = <<EOF
{
   "Version":"2012-10-17",
   "Statement":[
      {
        "Action": [
          "route53:ChangeResourceRecordSets",
          "route53:ListHostedZones",
          "route53:ListResourceRecordSets"
        ],
         "Effect":"Allow",
         "Resource":"*"
      },
      {
         "Action":[
            "logs:CreateLogGroup",
            "logs:CreateLogStream",
            "logs:PutLogEvents",
            "logs:GetLogEvents",
            "logs:DescribeLogStreams"
         ],
         "Effect":"Allow",
         "Resource":"*"
      }, 
      {
      "Action": ["s3:GetObject"],
      "Effect": "Allow",
      "Resource": "arn:aws:s3:::${var.bucket}/*"
    },
    {
      "Action": ["sns:Publish"],
      "Effect": "Allow",
      "Resource": "${var.alert}"
    },
    {
      "Action": ["ec2:DescribeVpcEndpoints"],
      "Effect": "Allow",
      "Resource": "*"
    }
   ]
}
EOF
}



resource "aws_lambda_function" "hsbc-dsn-switch-dr-lambda" {
  filename         = "${data.archive_file.lambda-zipper.output_path}"
  function_name    = "${var.name}"
  role             = "${aws_iam_role.hsbc-dsn-switch-dr-assumerole.arn}"
  handler          = "lambda_function.lambda_handler"
  runtime          = "python3.6"
  timeout          = "${var.timeout}"
  memory_size      = "${var.memory-size}"
  description      = "Lambda Function for notifying PAWS about Canopy alerts"
  source_code_hash = "${base64sha256("${data.archive_file.lambda-zipper.output_path}")}"
  depends_on       = ["data.archive_file.lambda-zipper"]
  environment {
    variables = {
      BUCKET     = "${var.bucket}",
      SNS        = "${var.alert}",
      CLUSTERSET = "${var.clusterset}"

    }
  }


}
