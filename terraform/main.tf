provider "aws" {
  region = "us-east-2"
}

data "aws_vpc" "default" {
  default = true
}

resource "aws_security_group" "app_server_sg"{
  name  = "aero-bound-ventures-sg"
  description = "Allow inbound traffic on ports 8000 and 22"
  vpc_id = data.aws_vpc.default.id

  ingress{
    from_port = 8000
    to_port = 8000
    protocol = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress{
    description = "HTTP for Nginx and Certbot"
    from_port = 80
    to_port = 80
    protocol = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress{
    description = "HTTPS for Nginx"
    from_port = 443
    to_port = 443
    protocol = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  ingress{
    description = "SSH access for debugging"
    from_port = 22
    to_port = 22
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
  key_name      = var.key_pair_name
  
  user_data = templatefile("./setup.sh", {
    repo_url                    = var.repo_url,
    gh_pat                      = var.gh_pat,
    mail_username               = var.mail_username,
    mail_password               = var.mail_password,
    mail_from                   = var.mail_from,
    mail_port                   = var.mail_port,
    mail_server                 = var.mail_server,
    access_token_expire_minutes = var.access_token_expire_minutes,
    secret_key                  = var.secret_key,
    algorithm                   = var.algorithm,
    amadeus_api_key             = var.amadeus_api_key,
    amadeus_api_secret          = var.amadeus_api_secret,
    amadeus_base_url            = var.amadeus_base_url,
    database_url                = var.database_url,
    pesapal_consumer_key        = var.pesapal_consumer_key,
    pesapal_consumer_secret     = var.pesapal_consumer_secret,
    pesapal_base_url            = var.pesapal_base_url,
    pesapal_ipn_id              = var.pesapal_ipn_id,
    cloudinary_url              = var.cloudinary_url,
    redis_url                   = var.redis_url,
    google_client_id            = var.google_client_id,
    google_client_secret        = var.google_client_secret,
    google_redirect_uri         = var.google_redirect_uri,
    cors_origins                = var.cors_origins,
    frontend_url                = var.frontend_url,
    environment                 = var.environment
  })

  vpc_security_group_ids = [aws_security_group.app_server_sg.id]

  tags = {
    Name = var.instance_name
  }
}

resource "aws_eip" "app_eip" {
  instance = aws_instance.app_server.id
  domain   = "vpc"
  
  tags = {
    Name = "${var.instance_name}-eip"
  }
}
