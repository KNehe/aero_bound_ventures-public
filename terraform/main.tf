provider "aws" {
  region = "us-east-2"
}

data "aws_vpc" "default" {
  default = true
}

resource "aws_security_group" "app_server_sg"{
  name  = "app-server-sg"
  description = "Allow inbound traffic on port 80"
  vpc_id = data.aws_vpc.default.id

  ingress{
    from_port = 8000
    to_port = 8000
    protocol = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  egress{
    from_port = 0
    to_port = 0
    protocol = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

data "aws_ami" "ubuntu" {
  most_recent = true

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*"]
  }

  owners = ["099720109477"] # Canonical
}

resource "aws_instance" "app_server" {
  ami           = data.aws_ami.ubuntu.id
  instance_type = var.instance_type
  user_data = templatefile("./setup.sh", {
    repo_url = var.repo_url
    gh_pat = var.gh_pat
    mail_username = var.mail_username
    mail_password = var.mail_password
    mail_from = var.mail_from
    mail_port = var.mail_port
    mail_server = var.mail_server
    access_token_expire_minutes = var.access_token_expire_minutes
    secret_key = var.secret_key
    algorithm = var.algorithm
    amadeus_api_key = var.amadeus_api_key
    amadeus_api_secret = var.amadeus_api_secret
    amadeus_base_url = var.amadeus_base_url
  })

  vpc_security_group_ids = [aws_security_group.app_server_sg.id]

  tags = {
    Name = var.instance_name
  }
}

