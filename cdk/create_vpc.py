#!/usr/bin/env python3
"""
Production VPC Creation Script using boto3
Creates a VPC with 3 public and 3 private subnets across 3 AZs with 1 NAT Gateway
"""

import boto3
import sys
from botocore.exceptions import ClientError

class VPCCreator:
    def __init__(self, region='ap-south-1', environment='Production'):
        self.ec2 = boto3.client('ec2', region_name=region)
        self.region = region
        self.environment = environment
        self.vpc_id = None
        self.igw_id = None
        self.nat_gateway_id = None
        self.public_subnets = []
        self.private_subnets = []
        
    def create_vpc(self, cidr='10.0.0.0/16'):
        """Create VPC"""
        print(f"Creating VPC with CIDR {cidr}...")
        response = self.ec2.create_vpc(
            CidrBlock=cidr,
            TagSpecifications=[{
                'ResourceType': 'vpc',
                'Tags': [{'Key': 'Name', 'Value': f'{self.environment}-VPC'}]
            }]
        )
        self.vpc_id = response['Vpc']['VpcId']
        
        # Enable DNS hostnames
        self.ec2.modify_vpc_attribute(VpcId=self.vpc_id, EnableDnsHostnames={'Value': True})
        self.ec2.modify_vpc_attribute(VpcId=self.vpc_id, EnableDnsSupport={'Value': True})
        
        print(f"VPC created: {self.vpc_id}")
        return self.vpc_id
    
    def create_internet_gateway(self):
        """Create and attach Internet Gateway"""
        print("Creating Internet Gateway...")
        response = self.ec2.create_internet_gateway(
            TagSpecifications=[{
                'ResourceType': 'internet-gateway',
                'Tags': [{'Key': 'Name', 'Value': f'{self.environment}-IGW'}]
            }]
        )
        self.igw_id = response['InternetGateway']['InternetGatewayId']
        
        self.ec2.attach_internet_gateway(
            InternetGatewayId=self.igw_id,
            VpcId=self.vpc_id
        )
        print(f"Internet Gateway created and attached: {self.igw_id}")
        return self.igw_id
    
    def create_subnets(self):
        """Create public and private subnets"""
        azs = self.ec2.describe_availability_zones()['AvailabilityZones'][:3]
        
        public_cidrs = ['10.0.1.0/24', '10.0.2.0/24', '10.0.3.0/24']
        private_cidrs = ['10.0.11.0/24', '10.0.12.0/24', '10.0.13.0/24']
        
        # Create public subnets
        for i, (az, cidr) in enumerate(zip(azs, public_cidrs), 1):
            print(f"Creating Public Subnet {i}...")
            response = self.ec2.create_subnet(
                VpcId=self.vpc_id,
                CidrBlock=cidr,
                AvailabilityZone=az['ZoneName'],
                TagSpecifications=[{
                    'ResourceType': 'subnet',
                    'Tags': [{'Key': 'Name', 'Value': f'{self.environment}-Public-Subnet-AZ{i}'}]
                }]
            )
            subnet_id = response['Subnet']['SubnetId']
            self.public_subnets.append(subnet_id)
            
            # Enable auto-assign public IP
            self.ec2.modify_subnet_attribute(
                SubnetId=subnet_id,
                MapPublicIpOnLaunch={'Value': True}
            )
            print(f"Public Subnet {i} created: {subnet_id}")
        
        # Create private subnets
        for i, (az, cidr) in enumerate(zip(azs, private_cidrs), 1):
            print(f"Creating Private Subnet {i}...")
            response = self.ec2.create_subnet(
                VpcId=self.vpc_id,
                CidrBlock=cidr,
                AvailabilityZone=az['ZoneName'],
                TagSpecifications=[{
                    'ResourceType': 'subnet',
                    'Tags': [{'Key': 'Name', 'Value': f'{self.environment}-Private-Subnet-AZ{i}'}]
                }]
            )
            subnet_id = response['Subnet']['SubnetId']
            self.private_subnets.append(subnet_id)
            print(f"Private Subnet {i} created: {subnet_id}")
    
    def create_nat_gateway(self):
        """Create NAT Gateway with Elastic IP"""
        print("Allocating Elastic IP...")
        eip_response = self.ec2.allocate_address(
            Domain='vpc',
            TagSpecifications=[{
                'ResourceType': 'elastic-ip',
                'Tags': [{'Key': 'Name', 'Value': f'{self.environment}-NAT-EIP'}]
            }]
        )
        allocation_id = eip_response['AllocationId']
        print(f"Elastic IP allocated: {eip_response['PublicIp']}")
        
        print("Creating NAT Gateway...")
        response = self.ec2.create_nat_gateway(
            SubnetId=self.public_subnets[0],
            AllocationId=allocation_id,
            TagSpecifications=[{
                'ResourceType': 'natgateway',
                'Tags': [{'Key': 'Name', 'Value': f'{self.environment}-NAT'}]
            }]
        )
        self.nat_gateway_id = response['NatGateway']['NatGatewayId']
        print(f"NAT Gateway created: {self.nat_gateway_id}")
        
        # Wait for NAT Gateway to be available
        print("Waiting for NAT Gateway to become available...")
        waiter = self.ec2.get_waiter('nat_gateway_available')
        waiter.wait(NatGatewayIds=[self.nat_gateway_id])
        print("NAT Gateway is now available")
        
        return self.nat_gateway_id
    
    def create_route_tables(self):
        """Create and configure route tables"""
        # Create public route table
        print("Creating Public Route Table...")
        public_rt_response = self.ec2.create_route_table(
            VpcId=self.vpc_id,
            TagSpecifications=[{
                'ResourceType': 'route-table',
                'Tags': [{'Key': 'Name', 'Value': f'{self.environment}-Public-RT'}]
            }]
        )
        public_rt_id = public_rt_response['RouteTable']['RouteTableId']
        
        # Add route to Internet Gateway
        self.ec2.create_route(
            RouteTableId=public_rt_id,
            DestinationCidrBlock='0.0.0.0/0',
            GatewayId=self.igw_id
        )
        
        # Associate public subnets
        for subnet_id in self.public_subnets:
            self.ec2.associate_route_table(
                RouteTableId=public_rt_id,
                SubnetId=subnet_id
            )
        print(f"Public Route Table created and associated: {public_rt_id}")
        
        # Create private route table
        print("Creating Private Route Table...")
        private_rt_response = self.ec2.create_route_table(
            VpcId=self.vpc_id,
            TagSpecifications=[{
                'ResourceType': 'route-table',
                'Tags': [{'Key': 'Name', 'Value': f'{self.environment}-Private-RT'}]
            }]
        )
        private_rt_id = private_rt_response['RouteTable']['RouteTableId']
        
        # Add route to NAT Gateway
        self.ec2.create_route(
            RouteTableId=private_rt_id,
            DestinationCidrBlock='0.0.0.0/0',
            NatGatewayId=self.nat_gateway_id
        )
        
        # Associate private subnets
        for subnet_id in self.private_subnets:
            self.ec2.associate_route_table(
                RouteTableId=private_rt_id,
                SubnetId=subnet_id
            )
        print(f"Private Route Table created and associated: {private_rt_id}")
    
    def create_infrastructure(self):
        """Create complete VPC infrastructure"""
        try:
            self.create_vpc()
            self.create_internet_gateway()
            self.create_subnets()
            self.create_nat_gateway()
            self.create_route_tables()
            
            print("\n" + "="*60)
            print("VPC Infrastructure Created Successfully!")
            print("="*60)
            print(f"VPC ID: {self.vpc_id}")
            print(f"Internet Gateway: {self.igw_id}")
            print(f"NAT Gateway: {self.nat_gateway_id}")
            print(f"Public Subnets: {', '.join(self.public_subnets)}")
            print(f"Private Subnets: {', '.join(self.private_subnets)}")
            print("="*60)
            
            return {
                'vpc_id': self.vpc_id,
                'igw_id': self.igw_id,
                'nat_gateway_id': self.nat_gateway_id,
                'public_subnets': self.public_subnets,
                'private_subnets': self.private_subnets
            }
            
        except ClientError as e:
            print(f"Error: {e}")
            sys.exit(1)

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Create Production VPC Infrastructure')
    parser.add_argument('--region', default='ap-south-1', help='AWS Region (default: ap-south-1)')
    parser.add_argument('--environment', default='Production', help='Environment name (default: Production)')
    parser.add_argument('--cidr', default='10.0.0.0/16', help='VPC CIDR block (default: 10.0.0.0/16)')
    
    args = parser.parse_args()
    
    creator = VPCCreator(region=args.region, environment=args.environment)
    creator.create_infrastructure()
