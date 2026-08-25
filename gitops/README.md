# Staging GitOps

Argo CD owns the staging backend and backend DopplerSecret. Terraform and the
staging infrastructure workflow continue to own AWS resources, EKS bootstrap,
the Doppler Operator, and cluster authentication Secrets.

## Required GitHub secret

Create a read-only SSH deploy key for this repository and store its private key
as the `ARGOCD_REPO_SSH_PRIVATE_KEY` Actions secret. Add the matching public key
to the repository as a deploy key without write access. Argo CD uses that key to
read the private repository; the key is never stored in Git.

## Reconciliation

The infrastructure workflow installs the pinned Argo CD chart, configures the
repository credential, and applies `gitops/staging/root-application.yaml`. The
root Application creates the staging AppProject and child Applications. Sync
waves create the DopplerSecret Application before the backend Application.

The deployment workflow tests the backend, pushes an image tagged with the source
commit SHA, and changes only `gitops/staging/values/backend.yaml`. Argo CD polls
Git and reconciles that image tag. The workflow waits for the Argo CD Application
and Kubernetes rollouts before running the existing smoke test.

## Private UI access

```bash
kubectl -n argocd port-forward service/argocd-server 8080:80
kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath='{.data.password}' | base64 --decode
```

Open `http://localhost:8080` and sign in as `admin`. Rotate or delete the initial
admin Secret after configuring the permanent authentication method.

## Drift demonstration

Change a safe, Git-owned value and watch self-healing restore it:

```bash
kubectl -n aero-staging scale deployment/aero-backend-api --replicas=2
kubectl -n aero-staging get deployment/aero-backend-api --watch
```

## Rollback

Revert the desired-state commit that changed `image.tag`, then push the revert.
Do not run `helm rollback` or patch the live Deployment because Argo CD will
restore the value declared in Git.

## Destroying staging

Use only the infrastructure workflow's `destroy` operation. It deletes the
`aero-staging-root` Application first so Argo CD stops reconciling and cascades
deletion to the backend and its Ingress. The workflow then removes any remaining
Ingress before running `terraform destroy`, allowing the AWS load balancer to be
cleaned up before EKS disappears.
