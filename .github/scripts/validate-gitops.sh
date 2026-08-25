#!/usr/bin/env bash

set -euo pipefail

repository_root="$(git rev-parse --show-toplevel)"
cd "${repository_root}"

required_files=(
  .github/workflows/deploy-backend-staging.yml
  .github/workflows/staging-backend.yml
  .github/workflows/terraform-kubernetes-staging.yml
  .github/workflows/validate-gitops.yml
  gitops/bootstrap/argocd-values.yaml
  gitops/staging/root-application.yaml
  gitops/staging/applications/project.yaml
  gitops/staging/applications/backend-secrets.yaml
  gitops/staging/applications/backend.yaml
  gitops/staging/values/backend-secrets.yaml
  gitops/staging/values/backend.yaml
)

for required_file in "${required_files[@]}"; do
  if [[ ! -f "${required_file}" ]]; then
    echo "Missing GitOps file: ${required_file}" >&2
    exit 1
  fi
done

ruby -ryaml -e '
  ARGV.each do |path|
    documents = YAML.load_stream(File.read(path))
    abort("#{path} contains no YAML document") if documents.empty?
  rescue Psych::SyntaxError => error
    abort("#{path}: #{error.message}")
  end
' "${required_files[@]}"

rg --quiet --fixed-strings 'repoURL: git@github.com:KNehe/aero_bound_ventures.git' \
  gitops/staging/root-application.yaml \
  gitops/staging/applications/backend-secrets.yaml \
  gitops/staging/applications/backend.yaml
rg --quiet --fixed-strings 'prune: true' gitops/staging/root-application.yaml
rg --quiet --fixed-strings 'selfHeal: true' gitops/staging/root-application.yaml
rg --quiet --fixed-strings 'argocd.argoproj.io/sync-wave: "-1"' \
  gitops/staging/applications/backend-secrets.yaml
rg --quiet --fixed-strings 'argocd.argoproj.io/sync-wave: "0"' \
  gitops/staging/applications/backend.yaml

helm lint helm/backend --strict \
  -f helm/backend/values-staging.yaml \
  -f gitops/staging/values/backend.yaml
helm template aero-backend helm/backend \
  --namespace aero-staging \
  -f helm/backend/values-staging.yaml \
  -f gitops/staging/values/backend.yaml >/dev/null

helm lint helm/backend-secrets --strict \
  -f gitops/staging/values/backend-secrets.yaml
helm template aero-backend-secrets helm/backend-secrets \
  --namespace doppler-operator-system \
  -f gitops/staging/values/backend-secrets.yaml >/dev/null

if rg --quiet --fixed-strings \
  'helm upgrade --install aero-backend helm/backend' \
  .github/workflows/deploy-backend-staging.yml; then
  echo "The staging deployment workflow still directly owns the backend Helm release." >&2
  exit 1
fi

rg --quiet --fixed-strings 'contents: write' \
  .github/workflows/deploy-backend-staging.yml
rg --quiet --fixed-strings 'gitops/staging/values/backend.yaml' \
  .github/workflows/deploy-backend-staging.yml
rg --quiet --fixed-strings 'argo-cd --version 10.2.1' \
  .github/workflows/terraform-kubernetes-staging.yml
rg --quiet --fixed-strings 'gitops/staging/root-application.yaml' \
  .github/workflows/terraform-kubernetes-staging.yml
rg --quiet --fixed-strings 'bash .github/scripts/validate-gitops.sh' \
  .github/workflows/validate-gitops.yml
rg --quiet --fixed-strings 'sudo apt-get install --yes ripgrep' \
  .github/workflows/validate-gitops.yml

if rg --quiet --fixed-strings \
  -- \
  "--for=jsonpath='{.status.sync.status}'=Synced" \
  .github/workflows/terraform-kubernetes-staging.yml; then
  echo "Bootstrap must not wait for the root Application to become fully synced." >&2
  exit 1
fi

rg --quiet --fixed-strings \
  'get applications --output wide' \
  .github/workflows/terraform-kubernetes-staging.yml
rg --quiet --fixed-strings \
  'describe application/aero-staging-root' \
  .github/workflows/terraform-kubernetes-staging.yml

ruby -ryaml -e '
  workflow = YAML.load_file(ARGV.fetch(0))
  steps = workflow.fetch("jobs").fetch("terraform").fetch("steps")
  destroy = steps.find { |step| step["name"] == "Destroy staging infrastructure" }
  abort("Destroy staging infrastructure step is missing") unless destroy

  script = destroy.fetch("run")
  root_delete = script.index("delete application/aero-staging-root")
  ingress_delete = script.index("delete ingress/aero-backend-api")
  terraform_destroy = script.index("destroy -input=false -auto-approve")

  unless root_delete && ingress_delete && terraform_destroy &&
         root_delete < ingress_delete && ingress_delete < terraform_destroy
    abort("Destroy must remove the Argo CD root before the Ingress and Terraform resources")
  end
' .github/workflows/terraform-kubernetes-staging.yml

ruby -ryaml -e '
  values = YAML.load_file(ARGV.fetch(0))
  health_check = values.dig(
    "configs",
    "cm",
    "resource.customizations.health.argoproj.io_Application"
  )

  unless health_check&.include?(%q(obj.status.sync.status == "Synced"))
    abort("Child Application health must become Healthy when synchronization completes")
  end
' gitops/bootstrap/argocd-values.yaml

echo "GitOps contract validation passed."
