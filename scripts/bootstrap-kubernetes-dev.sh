#!/usr/bin/env bash

# Bootstrap Doppler-backed configuration and deploy the backend to local k3d.
# Windows users should run this script from WSL2.
#
# Prerequisites: a running k3d cluster, the backend image loaded into that
# cluster, and authenticated doppler, helm, and kubectl CLIs.
#
# Run from the repository root:
#   ./scripts/bootstrap-kubernetes-dev.sh

set -euo pipefail

KUBERNETES_CONTEXT="k3d-aero-backend-dev"
KUBERNETES_NAMESPACE="aero-dev"
BACKEND_VALUES="helm/backend/values-dev.yaml"
OPERATOR_NAMESPACE="doppler-operator-system"
OPERATOR_RELEASE="doppler-operator"
TOKEN_SECRET_NAME="doppler-token-secret"
DOPPLER_SECRET_RELEASE="aero-backend-secrets"
DOPPLER_SECRET_NAME="aero-backend"
BACKEND_RELEASE="aero-backend"

# Read the developer's project and config selected by doppler setup.
DOPPLER_PROJECT="$(doppler configure get project --plain)"
DOPPLER_CONFIG="$(doppler configure get config --plain)"

printf 'Using Kubernetes context: %s\n' "${KUBERNETES_CONTEXT}"
printf 'Using application namespace: %s\n' "${KUBERNETES_NAMESPACE}"
printf 'Using Doppler project/config: %s/%s\n' "${DOPPLER_PROJECT}" "${DOPPLER_CONFIG}"

# Create a temporary, read-only token for the selected Doppler config. Command
# substitution captures the token so it is never printed to the terminal.
token_name="k3d-$(date -u +%Y%m%d-%H%M%S)"
DOPPLER_SERVICE_TOKEN="$(
  doppler configs tokens create "${token_name}" \
    --project "${DOPPLER_PROJECT}" \
    --config "${DOPPLER_CONFIG}" \
    --access read \
    --max-age 24h \
    --plain
)"

# Install or upgrade the cluster-wide Doppler controller at a pinned version.
helm repo add doppler https://helm.doppler.com --force-update
helm repo update doppler
helm upgrade --install "${OPERATOR_RELEASE}" doppler/doppler-kubernetes-operator \
  --kube-context "${KUBERNETES_CONTEXT}" \
  --namespace "${OPERATOR_NAMESPACE}" \
  --create-namespace \
  --version 1.5.7 \
  --wait \
  --timeout 2m

# Create the application namespace and update the operator's authentication
# Secret idempotently. The token is sent through stdin, not written to disk.
kubectl --context "${KUBERNETES_CONTEXT}" \
  create namespace "${KUBERNETES_NAMESPACE}" \
  --dry-run=client -o yaml |
  kubectl --context "${KUBERNETES_CONTEXT}" apply -f -

printf '%s' "${DOPPLER_SERVICE_TOKEN}" |
  kubectl --context "${KUBERNETES_CONTEXT}" \
  --namespace "${OPERATOR_NAMESPACE}" \
  create secret generic "${TOKEN_SECRET_NAME}" \
  --from-file=serviceToken=/dev/stdin \
  --dry-run=client -o yaml |
  kubectl --context "${KUBERNETES_CONTEXT}" apply -f -

# Lint with all required values. Linting this chart without these values emits
# missing-value warnings because they are intentionally absent from Git.
helm lint helm/backend-secrets --strict \
  --set-string "doppler.project=${DOPPLER_PROJECT}" \
  --set-string "doppler.config=${DOPPLER_CONFIG}" \
  --set-string "managedSecret.namespace=${KUBERNETES_NAMESPACE}"

# Create the DopplerSecret custom resource. The operator reads it and maintains
# the backend-secrets Kubernetes Secret in the application namespace.
helm upgrade --install "${DOPPLER_SECRET_RELEASE}" helm/backend-secrets \
  --kube-context "${KUBERNETES_CONTEXT}" \
  --namespace "${OPERATOR_NAMESPACE}" \
  --set-string "doppler.project=${DOPPLER_PROJECT}" \
  --set-string "doppler.config=${DOPPLER_CONFIG}" \
  --set-string "managedSecret.namespace=${KUBERNETES_NAMESPACE}"

# Do not deploy the migration, API, or worker until their Secret is available.
kubectl --context "${KUBERNETES_CONTEXT}" \
  --namespace "${OPERATOR_NAMESPACE}" wait \
  --for=condition=secrets.doppler.com/SecretSyncReady \
  "dopplersecret/${DOPPLER_SECRET_NAME}" \
  --timeout=120s

# These describe commands show status and key names without decoding values.
kubectl --context "${KUBERNETES_CONTEXT}" \
  --namespace "${OPERATOR_NAMESPACE}" \
  describe "dopplersecret/${DOPPLER_SECRET_NAME}"
kubectl --context "${KUBERNETES_CONTEXT}" \
  --namespace "${KUBERNETES_NAMESPACE}" \
  describe secret backend-secrets

# Validate the application chart before changing the release.
helm lint helm/backend --strict -f "${BACKEND_VALUES}"

# The migration hook runs first. Helm proceeds to the API and worker only when
# the migration succeeds. Reset old release values because the chart previously
# stored inline config and now uses only the Doppler-managed Secret.
helm upgrade --install "${BACKEND_RELEASE}" helm/backend \
  --kube-context "${KUBERNETES_CONTEXT}" \
  --namespace "${KUBERNETES_NAMESPACE}" \
  -f "${BACKEND_VALUES}" \
  --reset-values \
  --wait \
  --wait-for-jobs \
  --timeout 5m

kubectl --context "${KUBERNETES_CONTEXT}" \
  --namespace "${KUBERNETES_NAMESPACE}" \
  rollout status "deployment/${BACKEND_RELEASE}-api" --timeout=120s
kubectl --context "${KUBERNETES_CONTEXT}" \
  --namespace "${KUBERNETES_NAMESPACE}" \
  rollout status "deployment/${BACKEND_RELEASE}-worker" --timeout=120s

printf '\nBootstrap and deployment completed.\n'
printf 'In a second terminal, run:\n'
printf '  kubectl --context %s --namespace %s port-forward service/%s-api 8000:80\n' \
  "${KUBERNETES_CONTEXT}" "${KUBERNETES_NAMESPACE}" "${BACKEND_RELEASE}"
printf 'Then verify:\n'
printf '  curl http://localhost:8000/live\n'
printf '  curl http://localhost:8000/ready\n'
