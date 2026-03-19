# Deploy KeepContext AI on AWS Free Tier

This guide is tuned for a free-tier-conscious setup.

## Architecture (low-cost)

- EC2 `t3.micro` (or `t2.micro`) for app + ChromaDB
- Neo4j Aura Free for graph DB (recommended to avoid memory pressure on EC2)
- Security Group open only to required ports

## Before You Start

- Rotate any previously exposed API keys.
- Keep secrets in AWS Systems Manager Parameter Store or AWS Secrets Manager.
- Do not commit `.env.ec2`.

## 1. Create AWS resources

1. Launch EC2 Ubuntu 22.04/24.04.
2. Attach a security group:
   - Inbound `22` from your IP only
   - Inbound `8003` from your IP only (for initial validation)
3. Attach at least 20 GB gp3 EBS volume.

## 2. Prepare instance

SSH into EC2 and run:

```bash
sudo apt update -y
sudo apt install -y git
```

Copy and run bootstrap script:

```bash
chmod +x deploy/aws/ec2-bootstrap.sh
./deploy/aws/ec2-bootstrap.sh
```

Then logout/login once.

## 3. Clone and configure app

```bash
git clone <your-repo-url> keepcontext-ai
cd keepcontext-ai
cp deploy/aws/.env.ec2.example deploy/aws/.env.ec2
nano deploy/aws/.env.ec2
```

Set these values at minimum:

- `OPENAI_API_KEY`
- `GROQ_API_KEY`
- `NEO4J_URI`
- `NEO4J_USER`
- `NEO4J_PASSWORD`

## 4. Deploy stack

```bash
docker compose -f deploy/aws/docker-compose.free.yml up -d --build
```

## 5. Verify

```bash
docker compose -f deploy/aws/docker-compose.free.yml ps
curl http://<EC2_PUBLIC_IP>:8003/health
```

Expected health response includes:

- `status: healthy`
- `chroma: connected`
- `neo4j: connected` (if Aura credentials are valid)

## 6. Make it more reliable

Enable Docker on boot:

```bash
sudo systemctl enable docker
```

Because services use `restart: unless-stopped`, they recover on reboot once Docker starts.

## 7. Cost notes for free tier

- Free tier is time-limited and region-dependent.
- `t3.micro` has low memory; avoid running local Neo4j on this instance.
- If you see OOM or restarts, move to `t3.small`.

## 8. Optional production hardening

- Put Nginx/ALB in front with TLS.
- Restrict inbound to `443` only.
- Add CloudWatch alarms for CPU, memory (via agent), and container restarts.
