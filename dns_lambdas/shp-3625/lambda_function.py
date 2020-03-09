# -*- coding: utf-8 -*-
import json
import logging
import boto3
import os
import sys

logger = logging.getLogger()
logger.setLevel(logging.INFO)

BUCKET = os.environ['BUCKET']
CLUSTERSET = os.environ['CLUSTERSET']
ALERT = os.environ['SNS']


client = boto3.client('route53')


def send_email_alert(topic, message, custom_subject):
    client = boto3.client('sns')
    client.publish(
        TopicArn=topic,
        Subject=custom_subject,
        Message=message,
        MessageStructure='string',
    )

def retrieve_config(bucket, clusterset):
    s3 = boto3.resource('s3')
    content_object = s3.Object(bucket, "clusterset-{}.json".format(clusterset))
    file_content = content_object.get()['Body'].read().decode('utf-8')
    json_content = json.loads(file_content)
    return(json_content)


def update_dns_record(hostedzone, current_record):
    client.change_resource_record_sets(
            HostedZoneId=hostedzone,
            ChangeBatch={'Changes': 
            [{'Action': 'UPSERT', 'ResourceRecordSet': current_record}]
            }    
        )

def get_dns_config(name, hostedzone):
    pager = client.get_paginator('list_resource_record_sets')
    for rset in pager.paginate(HostedZoneId=hostedzone):
        for records in rset['ResourceRecordSets']:
            if records['Name'].replace(r'\052','*') == name:  #related to https://github.com/boto/boto/issues/818
                return (records)


def create_dns_record(name, hostedzone, targethostedzone, weight, target, setid):
  response = client.change_resource_record_sets(
    HostedZoneId = hostedzone,
    ChangeBatch = {
      'Changes': [{
        'Action': 'UPSERT',
        'ResourceRecordSet': {
          'Name': name,
          'Type': 'A',
          'AliasTarget': {
            'HostedZoneId': targethostedzone,
            'DNSName': target,
            'EvaluateTargetHealth': False
          },
          'Weight': weight,
          'SetIdentifier': setid,
        }
      }]}
  )
  return response

def check_vpc_endpoints(endpointname):
    client = boto3.client('ec2')
    response = client.describe_vpc_endpoints()
    for endpoints in response['VpcEndpoints']:
        for dnsentries in endpoints['DnsEntries']:
            if (dnsentries['DnsName']) == endpointname:
                return True
            else:
                return False


def lambda_handler(event, context):

    
    logger.info("EVENT: {}".format(event))
    logger.info("ENV VARS:{} {} {}".format(BUCKET, CLUSTERSET, ALERT))

    for events in event['Records']:
        logger.info("EVENT NAME:{}".format(events['eventName']))
        if events['eventName'] == "ObjectRemoved:Delete":
            logger.error("configuration file has been deleted")
            send_email_alert(os.environ['SNS'], "file deleted", "Config file deleted") #tbd by HSBC
            sys.exit(1)

    try:
        logger.info("trying to retrieve {}/clusterset-{}.json".format(BUCKET, CLUSTERSET))
        clusterset_s3_file = retrieve_config(BUCKET, CLUSTERSET)
    except client.exceptions.ClientError as e:
        logger.error("configuration file not found or permission error") #tbd by HSBC
        send_email_alert(os.environ['SNS'], str(e), "Config file error") #tbd by HSBC
        sys.exit(1)

    logger.info("#LOOPING CLUSTERS")
    logger.info("###") #spacing for logs
    for clusters in clusterset_s3_file['clusters']:
        dns_config = clusterset_s3_file['clusters'][clusters]['dns']
        status = clusterset_s3_file['clusters'][clusters]['status']
        cluster_config =  clusterset_s3_file['clusters'][clusters]

        logger.info("CLUSTER: {}".format(cluster_config['cluster_name']))
        logger.info("DNS NAME: {}".format(dns_config['dns_domain']))
        logger.info("WEIGHT IN CONF FILE: {}".format(dns_config['weight']))

        HOSTEDZONE = clusterset_s3_file['metadata']['dns']['zone_id']
        logger.info("HOSTED ZONE: {}".format(HOSTEDZONE))
        current_record = get_dns_config(dns_config['dns_domain'], HOSTEDZONE)
        if not get_dns_config(dns_config['dns_domain'], HOSTEDZONE):
            logger.warning("# RECORD NOT FOUND: CREATING RECORD")
            record_created = create_dns_record(
                dns_config['dns_domain'],
                HOSTEDZONE,
                dns_config['dns_target_alias_hosted_zone'],
                dns_config['weight'],
                dns_config['dns_target'],
                dns_config['setid']
                )
            logger.info("CREATED RECORD:{}".format(record_created))
        else:
            logger.info("CURRENT DNS RECORD: {}".format(current_record))
            logger.info("VCP ENDPOINT: {}".format(dns_config['dns_target']))
            if check_vpc_endpoints(dns_config['dns_target']):
                logger.info("# CONFIGURING RECORD")
                # updating the record with the values of the config file
                current_record['Weight'] = dns_config['weight']
                current_record['AliasTarget']['DNSName'] = dns_config['dns_target']
                current_record['AliasTarget']['HostedZoneId'] = dns_config['dns_target_alias_hosted_zone']
                update_dns_record(HOSTEDZONE, current_record)
                logger.info("NEW DNS RECORD: {}".format(current_record))
                logger.info("###") #spacing for logs
            else:
                logger.error("VPC ENDPOINT NOT FOUND")
                logger.info("###") #spacing for logs