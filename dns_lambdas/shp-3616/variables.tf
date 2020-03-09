variable "name" {
  type    = "string"
  default = "hsbc_clusterset_control"
}

variable "region" {
  type    = "string"
  default = "eu-west-1"
}

variable "timeout" {
  type    = "string"
  default = "300"
}

variable "memory-size" {
  description = "Amount of memory in MB your Lambda Function can use at runtime"
  type        = "string"
  default     = "512"
}


variable "bucket" {
  description = "bucket with cluster set config file"
  default     = "hsbc-poc-dr-3616"
}


variable "clusterset" {
  description = "clusterset id and bucket folder"
  default     = "clusterset123"
}

variable "alert" {
  description = "SNS topic ARN to send alerts"
  default     = "arn:aws:sns:eu-west-1:067099894743:testemailandtext"
}
