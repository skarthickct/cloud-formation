# AWS VPC Creation with Python Boto3

Python script to create production-ready VPC infrastructure using boto3.

## Features

- Creates VPC with 3 public and 3 private subnets across 3 AZs
- Single NAT Gateway for cost optimization
- Internet Gateway for public subnet connectivity
- Automatic route table configuration
- Proper tagging for all resources

## Prerequisites

- Python 3.7+
- AWS CLI configured with credentials
- boto3 library

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

```bash
python create_vpc.py
```

### Custom Configuration

```bash
# Specify region
python create_vpc.py --region us-east-1

# Specify environment name
python create_vpc.py --environment Staging

# Specify VPC CIDR
python create_vpc.py --cidr 172.16.0.0/16

# Combined
python create_vpc.py --region us-east-1 --environment Production --cidr 10.0.0.0/16
```

## Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--region` | ap-south-1 | AWS region to create resources |
| `--environment` | Production | Environment name for resource tagging |
| `--cidr` | 10.0.0.0/16 | VPC CIDR block |

## What Gets Created

### Network Resources
- 1 VPC (10.0.0.0/16)
- 1 Internet Gateway
- 3 Public Subnets (10.0.1.0/24, 10.0.2.0/24, 10.0.3.0/24)
- 3 Private Subnets (10.0.11.0/24, 10.0.12.0/24, 10.0.13.0/24)

### Routing
- 1 Public Route Table (routes to Internet Gateway)
- 1 Private Route Table (routes to NAT Gateway)

### NAT & Connectivity
- 1 NAT Gateway in first public subnet
- 1 Elastic IP for NAT Gateway

## Output

The script outputs:
- VPC ID
- Internet Gateway ID
- NAT Gateway ID
- List of Public Subnet IDs
- List of Private Subnet IDs

## Example Output

```
Creating VPC with CIDR 10.0.0.0/16...
VPC created: vpc-0123456789abcdef0
Creating Internet Gateway...
Internet Gateway created and attached: igw-0123456789abcdef0
Creating Public Subnet 1...
Public Subnet 1 created: subnet-0123456789abcdef0
...
============================================================
VPC Infrastructure Created Successfully!
============================================================
VPC ID: vpc-0123456789abcdef0
Internet Gateway: igw-0123456789abcdef0
NAT Gateway: nat-0123456789abcdef0
Public Subnets: subnet-xxx, subnet-yyy, subnet-zzz
Private Subnets: subnet-aaa, subnet-bbb, subnet-ccc
============================================================
```

## Cost Considerations

- NAT Gateway: ~$32/month ($0.045/hour)
- Data processing: $0.045/GB
- Elastic IP: Free when attached

## Cleanup

To delete the VPC and all resources, use the AWS Console or CLI:

```bash
# Delete NAT Gateway first
aws ec2 delete-nat-gateway --nat-gateway-id <nat-gateway-id> --region ap-south-1

# Wait for NAT Gateway deletion (takes a few minutes)
# Then release Elastic IP
aws ec2 release-address --allocation-id <allocation-id> --region ap-south-1

# Delete subnets
aws ec2 delete-subnet --subnet-id <subnet-id> --region ap-south-1

# Detach and delete Internet Gateway
aws ec2 detach-internet-gateway --internet-gateway-id <igw-id> --vpc-id <vpc-id> --region ap-south-1
aws ec2 delete-internet-gateway --internet-gateway-id <igw-id> --region ap-south-1

# Delete VPC
aws ec2 delete-vpc --vpc-id <vpc-id> --region ap-south-1
```

## Error Handling

The script includes error handling for common issues:
- AWS credential problems
- Insufficient permissions
- Resource quota limits
- Network conflicts

## AWS Permissions Required

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ec2:CreateVpc",
        "ec2:CreateSubnet",
        "ec2:CreateInternetGateway",
        "ec2:CreateNatGateway",
        "ec2:CreateRouteTable",
        "ec2:CreateRoute",
        "ec2:AllocateAddress",
        "ec2:AttachInternetGateway",
        "ec2:AssociateRouteTable",
        "ec2:ModifyVpcAttribute",
        "ec2:ModifySubnetAttribute",
        "ec2:DescribeAvailabilityZones",
        "ec2:DescribeNatGateways",
        "ec2:CreateTags"
      ],
      "Resource": "*"
    }
  ]
}
```

## Comparison with CloudFormation

| Aspect | Boto3 Script | CloudFormation |
|--------|--------------|----------------|
| Execution | Immediate | Async (3-5 min) |
| Rollback | Manual | Automatic |
| Updates | Manual | Declarative |
| State | Not tracked | Tracked by AWS |
| Flexibility | High | Medium |
| Best For | Quick setup, automation | Production, IaC |

## Troubleshooting

### Issue: "UnauthorizedOperation"
**Solution:** Check AWS credentials and IAM permissions

### Issue: "VpcLimitExceeded"
**Solution:** Delete unused VPCs or request limit increase

### Issue: "AddressLimitExceeded"
**Solution:** Release unused Elastic IPs or request limit increase

## Next Steps

After VPC creation:
1. Create security groups
2. Deploy EC2 instances or EKS clusters
3. Set up VPC Flow Logs
4. Configure CloudWatch monitoring

## License

MIT License
