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

def retrieve_config(bucket, clusterset):
    s3 = boto3.resource('s3')
    content_object = s3.Object(bucket, "clusterset-{}.json".format(clusterset))
    file_content = content_object.get()['Body'].read().decode('utf-8')
    json_content = json.loads(file_content)
    return(json_content)

def write_config(bucket, config, clusterset):
    s3 = boto3.resource('s3')
    response = s3.Object(bucket, "clusterset-{}.json".format(clusterset)).put(Body=json.dumps(config))
    return(response)


def set_active_cluster(config):
    #something
    return(config)

def change_cluster_status(config):
    #something
    return(config)

def add_cluster_to_config(config):
    #something
    return(config)
 
def remove_cluster(config):
    #something
    return(config)
 
def update_config(confg):
    #something
    return(config)

def create_cluster_set(confg):
    #something
    return("Clusterset created")
 
def lambda_handler(event, context):

    aaa = retrieve_config(BUCKET, CLUSTERSET)

    bbb = write_config(BUCKET, aaa, CLUSTERSET)

    print(bbb)
