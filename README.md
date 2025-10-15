# AWS Production VPC - CloudFormation Template

A production-ready AWS VPC infrastructure template with multi-AZ support, designed for high availability and cost optimization.

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Deployment](#deployment)
- [Outputs](#outputs)
- [Cost Analysis](#cost-analysis)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

## Features

- **Multi-AZ Deployment**: Resources distributed across 3 availability zones
- **Public & Private Subnets**: Separate network tiers for security
- **NAT Gateway**: Secure outbound internet access for private resources
- **Auto-scaling Ready**: Designed to support EKS, EC2 Auto Scaling, and RDS
- **Parameterized**: Easily customizable CIDR blocks and naming
- **Export Values**: Stack outputs available for cross-stack references
- **Production-Ready**: Follows AWS Well-Architected Framework principles

## Architecture

```
VPC (10.0.0.0/16)
│
├── Availability Zone 1
│   ├── Public Subnet (10.0.1.0/24)
│   │   └── NAT Gateway + EIP
│   └── Private Subnet (10.0.11.0/24)
│
├── Availability Zone 2
│   ├── Public Subnet (10.0.2.0/24)
│   └── Private Subnet (10.0.12.0/24)
│
└── Availability Zone 3
    ├── Public Subnet (10.0.3.0/24)
    └── Private Subnet (10.0.13.0/24)

Internet Gateway → Public Subnets
NAT Gateway → Private Subnets → Internet
```

### Network Components

| Component | Count | Purpose |
|-----------|-------|---------|
| VPC | 1 | Isolated network environment |
| Internet Gateway | 1 | Public internet access |
| NAT Gateway | 1 | Private subnet internet egress |
| Elastic IP | 1 | Static IP for NAT Gateway |
| Public Subnets | 3 | Internet-facing resources |
| Private Subnets | 3 | Internal resources |
| Route Tables | 2 | Traffic routing rules |

## Prerequisites

- AWS CLI installed and configured
- AWS account with appropriate permissions
- IAM permissions for VPC, EC2, and CloudFormation resources

### Required IAM Permissions

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "cloudformation:*",
        "ec2:*"
      ],
      "Resource": "*"
    }
  ]
}
```

## Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd cloudformation
```

### 2. Deploy the Stack

```bash
aws cloudformation create-stack \
  --stack-name prod-vpc \
  --template-body file://vpc-template.yaml \
  --region ap-south-1
```

### 3. Monitor Deployment

```bash
aws cloudformation wait stack-create-complete \
  --stack-name prod-vpc \
  --region ap-south-1
```

### 4. Verify Outputs

```bash
aws cloudformation describe-stacks \
  --stack-name prod-vpc \
  --region ap-south-1 \
  --query 'Stacks[0].Outputs'
```

## Configuration

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `EnvironmentName` | String | Production | Environment identifier for resource tagging |
| `VpcCIDR` | String | 10.0.0.0/16 | VPC CIDR block |
| `PublicSubnet1CIDR` | String | 10.0.1.0/24 | Public subnet in AZ1 |
| `PublicSubnet2CIDR` | String | 10.0.2.0/24 | Public subnet in AZ2 |
| `PublicSubnet3CIDR` | String | 10.0.3.0/24 | Public subnet in AZ3 |
| `PrivateSubnet1CIDR` | String | 10.0.11.0/24 | Private subnet in AZ1 |
| `PrivateSubnet2CIDR` | String | 10.0.12.0/24 | Private subnet in AZ2 |
| `PrivateSubnet3CIDR` | String | 10.0.13.0/24 | Private subnet in AZ3 |

### Custom Configuration Example

```bash
aws cloudformation create-stack \
  --stack-name staging-vpc \
  --template-body file://vpc-template.yaml \
  --region ap-south-1 \
  --parameters \
    ParameterKey=EnvironmentName,ParameterValue=Staging \
    ParameterKey=VpcCIDR,ParameterValue=172.16.0.0/16 \
    ParameterKey=PublicSubnet1CIDR,ParameterValue=172.16.1.0/24
```

## Deployment

### Standard Deployment

```bash
aws cloudformation create-stack \
  --stack-name prod-vpc \
  --template-body file://vpc-template.yaml \
  --region <your-region>
```

### Deployment with Change Sets (Recommended for Updates)

```bash
# Create change set
aws cloudformation create-change-set \
  --stack-name prod-vpc \
  --change-set-name update-$(date +%Y%m%d-%H%M%S) \
  --template-body file://vpc-template.yaml \
  --region <your-region>

# Review changes
aws cloudformation describe-change-set \
  --stack-name prod-vpc \
  --change-set-name <change-set-name> \
  --region <your-region>

# Execute change set
aws cloudformation execute-change-set \
  --stack-name prod-vpc \
  --change-set-name <change-set-name> \
  --region <your-region>
```

### Validation

Validate template syntax before deployment:

```bash
aws cloudformation validate-template \
  --template-body file://vpc-template.yaml
```

## Outputs

The stack exports the following values for use in other CloudFormation stacks:

| Output | Export Name | Description |
|--------|-------------|-------------|
| VPCId | `${StackName}-VPC` | VPC identifier |
| PublicSubnets | `${StackName}-PublicSubnets` | Comma-separated public subnet IDs |
| PrivateSubnets | `${StackName}-PrivateSubnets` | Comma-separated private subnet IDs |
| PublicSubnet1 | `${StackName}-PublicSubnet1` | Public subnet 1 ID |
| PublicSubnet2 | `${StackName}-PublicSubnet2` | Public subnet 2 ID |
| PublicSubnet3 | `${StackName}-PublicSubnet3` | Public subnet 3 ID |
| PrivateSubnet1 | `${StackName}-PrivateSubnet1` | Private subnet 1 ID |
| PrivateSubnet2 | `${StackName}-PrivateSubnet2` | Private subnet 2 ID |
| PrivateSubnet3 | `${StackName}-PrivateSubnet3` | Private subnet 3 ID |
| NatGateway | N/A | NAT Gateway ID |
| NatGatewayEIP | N/A | NAT Gateway Elastic IP |

### Using Exports in Other Stacks

```yaml
Resources:
  MyInstance:
    Type: AWS::EC2::Instance
    Properties:
      SubnetId: !ImportValue prod-vpc-PublicSubnet1
```

## Cost Analysis

### Monthly Cost Breakdown (ap-south-1 Region)

| Resource | Unit Cost | Monthly Cost |
|----------|-----------|--------------|
| NAT Gateway | $0.045/hour | ~$32.40 |
| Data Processing | $0.045/GB | Variable |
| Elastic IP (attached) | $0.00 | $0.00 |
| **Total Base Cost** | | **~$32.40** |

### Cost Optimization Options

1. **Single NAT Gateway** (Current): ~$32/month
   - Lower cost
   - Single point of failure
   - Suitable for dev/test

2. **Multi-NAT Gateway**: ~$97/month
   - High availability
   - No single point of failure
   - Recommended for production

3. **NAT Instance**: ~$10-20/month
   - Lowest cost
   - Requires management
   - Lower throughput

### Reducing Costs

- Use VPC endpoints for AWS services (S3, DynamoDB)
- Schedule NAT Gateway for non-production environments
- Monitor data transfer with CloudWatch

## Best Practices

### Security

- [ ] Enable VPC Flow Logs for network monitoring
- [ ] Implement Network ACLs for additional security layer
- [ ] Use Security Groups to control instance-level traffic
- [ ] Enable AWS GuardDuty for threat detection
- [ ] Restrict SSH/RDP access to bastion hosts only

### High Availability

- [ ] Deploy resources across multiple AZs
- [ ] Use Auto Scaling Groups for EC2 instances
- [ ] Implement health checks and automated recovery
- [ ] Consider multi-NAT Gateway for critical workloads

### Monitoring

```bash
# Enable VPC Flow Logs
aws ec2 create-flow-logs \
  --resource-type VPC \
  --resource-ids <vpc-id> \
  --traffic-type ALL \
  --log-destination-type cloud-watch-logs \
  --log-group-name /aws/vpc/flowlogs
```

### Tagging Strategy

All resources are tagged with:
- `Name`: Descriptive resource name
- Environment can be customized via `EnvironmentName` parameter

Additional recommended tags:
- `Project`
- `Owner`
- `CostCenter`
- `Compliance`

## Troubleshooting

### Stack Creation Fails

**Check stack events:**
```bash
aws cloudformation describe-stack-events \
  --stack-name prod-vpc \
  --region ap-south-1 \
  --max-items 20
```

### Common Issues

#### 1. Elastic IP Limit Exceeded

**Error:** `The maximum number of addresses has been reached`

**Solution:**
```bash
# Request limit increase
aws service-quotas request-service-quota-increase \
  --service-code ec2 \
  --quota-code L-0263D0A3 \
  --desired-value 10
```

#### 2. CIDR Block Conflicts

**Error:** `CIDR block conflicts with existing VPC`

**Solution:** Modify CIDR parameters to use non-overlapping ranges

#### 3. Insufficient Availability Zones

**Error:** `Not enough availability zones`

**Solution:** Deploy in a region with at least 3 AZs or modify template

### Validation Commands

```bash
# Check VPC
aws ec2 describe-vpcs --vpc-ids <vpc-id>

# Check subnets
aws ec2 describe-subnets --filters "Name=vpc-id,Values=<vpc-id>"

# Check NAT Gateway
aws ec2 describe-nat-gateways --filter "Name=vpc-id,Values=<vpc-id>"

# Check route tables
aws ec2 describe-route-tables --filters "Name=vpc-id,Values=<vpc-id>"
```

## Cleanup

### Delete Stack

```bash
aws cloudformation delete-stack \
  --stack-name prod-vpc \
  --region ap-south-1
```

### Wait for Deletion

```bash
aws cloudformation wait stack-delete-complete \
  --stack-name prod-vpc \
  --region ap-south-1
```

**Warning:** Ensure no resources (EC2, RDS, EKS, etc.) are using the VPC before deletion.

## Use Cases

### Suitable For

- EKS cluster deployments
- Multi-tier web applications
- Microservices architectures
- Database hosting (RDS, Aurora)
- Development and staging environments

### Example Integrations

- **EKS**: Deploy worker nodes in private subnets
- **RDS**: Multi-AZ database in private subnets
- **ALB**: Application Load Balancer in public subnets
- **Lambda**: VPC-enabled functions in private subnets

## Roadmap

- [ ] Add VPC Flow Logs configuration
- [ ] Include Network ACL templates
- [ ] Add Transit Gateway integration
- [ ] Support for IPv6
- [ ] VPC Peering examples
- [ ] AWS PrivateLink endpoints

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/improvement`)
3. Commit your changes (`git commit -am 'Add new feature'`)
4. Push to the branch (`git push origin feature/improvement`)
5. Create a Pull Request

### Development Guidelines

- Follow AWS CloudFormation best practices
- Test templates in a non-production environment
- Update documentation for any changes
- Include cost impact analysis for new resources

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

- **Issues**: Report bugs via GitHub Issues
- **Discussions**: Use GitHub Discussions for questions
- **AWS Support**: Contact AWS Support for account-specific issues

## Acknowledgments

- AWS CloudFormation documentation
- AWS Well-Architected Framework
- Community contributions and feedback

---

**Maintained by:** [Your Name/Organization]  
**Last Updated:** October 2025  
**Version:** 1.0.0
