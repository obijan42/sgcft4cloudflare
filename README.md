# sgcft4cloudflare
Generator of CloudFormation Template that creates security groups for whitelisting CloudFlare

## What?

Creates a CloudFormation Template based on the currently published list of public IP addresses. 
This will create 2 "Security Groups" which allows ingress from these IPs.  Each security group supports 1 port:
- Port 80
- Port 443  

### Example rule

```json

    "SGGenerated80Rule12": {
      "Type": "AWS::EC2::SecurityGroupIngress", 
      "Properties": {
        "ToPort": "80", 
        "IpProtocol": "tcp", 
        "CidrIp": "190.93.240.0/20", 
        "FromPort": "80"
      }, 
    }, 

```

### Meta Data

The template contains extra information that allows you to determine the version of the feed data and make decissions based on that.
The checksum will allow you to verify that the feed has remained unchanged.


```json
  "Metadata": {
    "Feed Source": "CloudFlare", 
    "BuiltOn": "2019-05-28T10:28:35.600478", 
    "Author": "janhert", 
    "Feed Checksum": "227e465a1db261a2bd00366dc7d6f3be", 
    "Version": "1", 
    "Feed Size": 21
  }

```



## Why?

If you use this CDN, all the incoming HTTP requests (either port 80 or 443) are supposed to come from the official list of public IPs.  
Allowing public access to your public instance or load balancer would allow an attacker to bypass the CDN and the security controls this presents.

This system allows one to easily provide full protection to your resources, while balancing the need for updates with the governance requirements.

### Alternatives

- Lambda function that runs on a schedule and updates secuirty groups directly
- Running AWS CLI on the results of a web requests


### Benefits of this approach
- No code running in the account.  
- No egress requirement for pulling in a feed inside the account
- The CloudFormation can be managed centrally and made part of a CI/CD pipeline.
- Security groups area part of critical security infrastructure and should be tightly "change controlled". 
This solution allows governance of every change.
- Decouple the generation of the infrastructure and it's execution.  Only the later needs IAM access.
- CloudFormation allows for features such as "Drift detection" and fixing
   

## How?

- Run the script
- Run the template to create the stack
- Place the Security Group on the instances and load balancers (decide to support HTTP, HTTPS or both)
- Re-run script on a regular basis
- Use "Update stack" to control changes

