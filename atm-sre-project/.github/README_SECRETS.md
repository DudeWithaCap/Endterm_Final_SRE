# GitHub Actions — Required Secrets

Before the CI/CD pipeline will work, add these 4 secrets to your repository.

**How to add a secret:**
GitHub → your repository → Settings → Secrets and variables → Actions → New repository secret

---

## Required Secrets

### `DOCKER_USERNAME`
Your Docker Hub username (e.g. `johndoe`).
- Find it at: https://hub.docker.com — top-right profile menu.

### `DOCKER_PASSWORD`
Your Docker Hub password **or** an access token (recommended over your real password).
- Generate a token at: Docker Hub → Account Settings → Security → New Access Token.
- Set permissions to **Read & Write**.

### `EC2_HOST`
The public IP address of your EC2 instance (e.g. `54.123.45.67`).
- Find it at: AWS Console → EC2 → Instances → your instance → Public IPv4 address.
- If using LocalStack, this is `localhost` or the LocalStack host IP.

### `EC2_SSH_KEY`
The **full contents** of your `.pem` private key file used to SSH into the EC2 instance.
- Open the `.pem` file in a text editor and copy everything including the `-----BEGIN RSA PRIVATE KEY-----` and `-----END RSA PRIVATE KEY-----` lines.
- The pipeline writes this to `~/.ssh/id_rsa` and uses it to SSH as `ubuntu@EC2_HOST`.

---

## Pipeline overview

| Job | What it does |
|-----|-------------|
| `build` | Builds all 7 service Docker images and pushes them to Docker Hub |
| `provision` | SSHes into EC2, pulls latest code, runs Ansible deploy playbook |
| `deploy` | Copies kubeconfig from EC2, applies K8s manifests, restarts deployments |
| `healthcheck` | Waits 30s then curls `/health` on all 7 services, fails if any returns non-200 |

The pipeline triggers automatically on every push to `main`.
