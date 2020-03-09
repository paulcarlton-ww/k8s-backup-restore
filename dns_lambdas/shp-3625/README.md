## DNS switch lambfa

This Lambda function updates a DNS record based on a configuration file in an S3 bucket. 

The function expects three parameters (currently passed as environment variables using TF): 


`BUCKET` = the AWS S3 bucket where that file can be found 

`CLUSTERSET` = the Clusterset name and S3 folder containing the configuration file.

`SNS` = The SNS topic ARN for notifications


### Usage: 

The lambda function is triggered by S3 events: “All object create events” and "All object delete events". 

### Deployment:

```
terraform init
terraform plan
terraform apply
```

### Configuration file

The function expect a configuration file with the following format: 


```
{
    "metadata": {
      "cluster_set": "SHPDEV",
      "cluster_set_drn_domain": "clusterset123",
      "cluster_set_internet_domain": "public URL for the cluster",
      "dns": {
        "zone_id": "Z3SQB39QLI1IEL"
      }
    },
    "status": {
      "date_created": "2020-03-06T20:57:09Z (ISO 8601)",
      "date_updated": "2020-03-06T20:57:09Z",
      "active_clusters": [
        "cl01",
        "cl02"
      ],
      "primary_cluster": "cl01"
  
    },
    "clusters": {
      "cl01": {
        "cluster_name": "demo",
        "eks_proxy": "proxy_url",
        "cluster_software": {
          "eks_version": "1.14",
          "istio_version": "1.4.2"
        },
        "dns": {
          "setid": "setid123",
          "weight": 85,
          "dns_domain": "*cluster2.domain.env.hsbc.com.",
          "dns_target": "vpce-029df954cadd23735-78qqbnyk.vpce-svc-0685e2fd7d24ce9ec.eu-west-1.vpce.amazonaws.com",
          "dns_target_alias_hosted_zone": "Z38GZ743OKFT7T"
        },
        "status": {
          "level": 1,
          "is_primary": true,
          "message": "Descriptive message of the cluster status like Maintenance",
          "date_created": "2020-03-06T20:57:09Z",
          "date_updated": "2020-03-06T20:57:09Z"
        }
      },
      "cl02": {
        "cluster_name": "demo2",
        "eks_proxy": "proxy_url",
        "cluster_software": {
          "eks_version": "1.14",
          "istio_version": "1.4.2"
        },
        "dns": {
          "setid": "setid123",
          "weight": 24,
          "dns_domain": "*cluster2.domain.env.hsbc.com.",
          "dns_target": "vpce-029df954cadd23735-78qqbnyk.vpce-svc-0685e2fd7d24ce9ec.eu-west-1.vpce.amazonaws.com",
          "dns_target_alias_hosted_zone": "Z38GZ743OKFT7T"
        },
        "status": {
          "level": 5,
          "is_primary": false,
          "message": "Descriptive message of the cluster status like Maintenance",
          "date_created": "2020-03-06T20:57:09Z",
          "date_updated": "2020-03-06T20:57:09Z"
        }
      }
    }
  }
```
