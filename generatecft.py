#!/usr/bin/env python

# Copyright 2017-2023 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You may
# not use this file except in compliance with the License. A copy of the License is located at
#
#        http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for
# the specific language governing permissions and limitations under the License.


import json
import logging
import os
import platform
import requests
import sys
import hashlib
import datetime

# Uncomment to enable low level debugging
logging.basicConfig(level=logging.DEBUG)


def getCFTTemplate(filename):
    with open(filename, 'r') as f:
        return json.load(f)


def GenerateInjectSGRule(IPList):
    obj = {};

    for port in [80, 443]:
        groupId = "SGGenerated{}".format(port)
        ruleCounter = 0
        obj[groupId] = {
            "Type": "AWS::EC2::SecurityGroup",
            "Properties": {
                "GroupName": "CloudFlareIngress{}".format(port),
                "GroupDescription": "Allow access from CloudFlare IP to port {}".format(port),
                "VpcId": {"Ref": "vpc"}}}
        for ip in IPList:
            ruleCounter += 1
            ruleID = groupId + "Rule{}".format(ruleCounter)

            if ':' in ip:
                cidrKey = "CidrIpv6"
            else:
                cidrKey = "CidrIp"

            obj[ruleID] = {
                "Type": "AWS::EC2::SecurityGroupIngress",
                "DependsOn": groupId,
                "Properties": {
                    "GroupId": {"Fn::GetAtt": [groupId, "GroupId"]},
                    "IpProtocol": "tcp", "FromPort": "{}".format(port),
                    "ToPort": "{}".format(port),
                    cidrKey: ip
                }}
    return obj


def getIPAddressFeedAll():
    urlsToGet = ['https://www.cloudflare.com/ips-v4', 'https://www.cloudflare.com/ips-v6']

    resultList = []
    for url in urlsToGet:
        resultList += getIPAddressFeed(url)
    resultList.sort()
    logging.debug(resultList)
    return resultList


def getIPAddressFeed(url):
    try:
        response = requests.get(url)
        response = response.text
    except requests.exceptions.RequestException as e:
        logging.warning("Failed to get URL " + url, e)
        return None
    # One record per row
    response = response.split("\n")

    # Filter out empties
    response = list(filter(lambda x: (len(x) > 8), response))

    #    logging.debug(response)
    #    print(response)
    return response


def create_bucket_policy(iplist, bucketname='$BUCKETNAME'):
    return {
        "Version": "2012-10-17", "Statement": [{
            "Sid": "AllowCDN", "Effect": "Allow", "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": f"arn:aws:s3:::{bucketname}/*",
            "Condition": {"IpAddress": {"aws:SourceIp": iplist}}
        }]}


def write_codes(payload, filen):
    with open(filen, 'w') as outfile:
        json.dump(payload, outfile, indent=2)


# ----------------------------------------------------------------------


def main(argv):
    print(("Running in Python v{}".format(platform.python_version())))

    logging.info("Starting convertor")

    try:
        templateObj = getCFTTemplate(sys.path[0] + '/BaseCFTTemplate.template')
    except:
        logging.error("Failed parsing input template")
        exit(1)

    iplist = getIPAddressFeedAll()

    if not iplist:
        logging.warning("No IP list found, exiting")
        exit(1)

    # https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-ec2-security-group-ingress.html

    feedHash = hashlib.md5(str(iplist).encode('utf-8')).hexdigest()
    feedLen = len(iplist)

    logging.info("Info Hash: {} , {} items ".format(feedHash, feedLen))

    tempObj = {}
    tempObj = GenerateInjectSGRule(iplist)

    if (tempObj):
        templateObj['Resources'].update(tempObj)

    templateObj["Metadata"] = ({
        "Author": os.environ.get('USER', os.environ.get('USERNAME', 'Unknown')),
        "Version": "1",
        "BuiltOn": datetime.datetime.now().isoformat(),
        "Feed Source": "CloudFlare",
        "Feed Size": feedLen,
        "Feed Checksum": feedHash
    })

    # logging.debug(json.dumps(templateObj, indent=4))
    if (templateObj):
        destFile = sys.path[0] + '/SecGroupCloudflare.template'
        logging.info("Writing to " + destFile)
        write_codes(templateObj, destFile)
    write_codes(create_bucket_policy(iplist), 'BucketPolicyExample.json')


if __name__ == '__main__':
    main(sys.argv[1:])
