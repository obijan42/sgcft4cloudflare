#!/usr/bin/env python

# import boto3
import json
import logging
import os
import platform
import requests
import sys

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
    return [u'103.21.244.0/22', u'103.22.200.0/22', u'103.31.4.0/22', u'104.16.0.0/12', u'108.162.192.0/18',
            u'131.0.72.0/22', u'141.101.64.0/18', u'162.158.0.0/15', u'172.64.0.0/13', u'173.245.48.0/20',
            u'188.114.96.0/20', u'190.93.240.0/20', u'197.234.240.0/22', u'198.41.128.0/17', u'2400:cb00::/32',
            u'2405:8100::/32', u'2405:b500::/32', u'2606:4700::/32', u'2803:f800::/32', u'2a06:98c0::/29',
            u'2c0f:f248::/32']

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

    tempObj = {}
    tempObj = GenerateInjectSGRule(iplist)

    if (tempObj):
        templateObj['Resources'].update(tempObj)

    # logging.debug(json.dumps(templateObj, indent=4))
    if (templateObj):
        destFile = sys.path[0] + '/SecGroupCloudflare.template'
        logging.info("Writing to " + destFile)
        with open(destFile, 'w') as f:
            f.writelines(json.dumps(templateObj, sort_keys=False, indent=2))
            f.close()


if __name__ == '__main__':
    main(sys.argv[1:])
