#!/usr/bin/env bash

set -euo pipefail

repository_root="$(git rev-parse --show-toplevel)"
cd "${repository_root}"

required_files=(
  .github/workflows/deploy-backend-staging.yml
  .github/workflows/staging-backend.yml
  .github/workflows/terraform-kubernetes-staging.yml
  gitops/bootstrap/argocd-values.yaml
  gitops/bootstrap/deploy-role-rbac.yaml
  gitops/staging/root-application.yaml
  gitops/staging/applications/project.yaml
  gitops/staging/applications/backend-secrets.yaml
  gitops/staging/applications/backend.yaml
  gitops/staging/applications/monitoring.yaml
  gitops/staging/values/backend-secrets.yaml
  gitops/staging/values/backend.yaml
  helm/monitoring/Chart.yaml
  helm/monitoring/Chart.lock
  helm/monitoring/values.yaml
)

for required_file in "${required_files[@]}"; do
  if [[ ! -f "${required_file}" ]]; then
    echo "Missing GitOps file: ${required_file}" >&2
    exit 1
  fi
done

if [[ -e .github/workflows/validate-gitops.yml ]]; then
  echo "GitOps validation must remain part of the staging pipeline." >&2
  exit 1
fi

ruby -ryaml -e '
  ARGV.each do |path|
    documents = YAML.load_stream(File.read(path))
    abort("#{path} contains no YAML document") if documents.empty?
  rescue Psych::SyntaxError => error
    abort("#{path}: #{error.message}")
  end
' "${required_files[@]}"

repository_files=(
  gitops/staging/root-application.yaml
  gitops/staging/applications/backend-secrets.yaml
  gitops/staging/applications/backend.yaml
  gitops/staging/applications/monitoring.yaml
)

for repository_file in "${repository_files[@]}"; do
  if ! rg --quiet --fixed-strings \
    'repoURL: git@github.com:KNehe/aero_bound_ventures.git' \
    "${repository_file}"; then
    echo "Unexpected repository URL in ${repository_file}" >&2
    exit 1
  fi
done

rg --quiet --fixed-strings 'prune: true' gitops/staging/root-application.yaml
rg --quiet --fixed-strings 'selfHeal: true' gitops/staging/root-application.yaml
rg --quiet --fixed-strings 'argocd.argoproj.io/sync-wave: "-1"' \
  gitops/staging/applications/backend-secrets.yaml
rg --quiet --fixed-strings 'argocd.argoproj.io/sync-wave: "0"' \
  gitops/staging/applications/backend.yaml
rg --quiet --fixed-strings 'argocd.argoproj.io/sync-wave: "1"' \
  gitops/staging/applications/monitoring.yaml
rg --quiet --fixed-strings '"grafana-staging.aeroboundventures.com"' \
  terraform/kubernetes-staging/variables.tf
rg --quiet --fixed-strings 'subject_alternative_names = [var.staging_grafana_hostname]' \
  terraform/kubernetes-staging/acm.tf
rg --quiet --fixed-strings 'name: "aero-staging"' \
  terraform/kubernetes-staging/alb-ingress-class.yaml.tftpl
rg --quiet --fixed-strings 'staging_certificate_validation_records' \
  .github/workflows/terraform-kubernetes-staging.yml
rg --quiet --fixed-strings 'STAGING_SHARED_ALB_ENABLED' \
  .github/workflows/terraform-kubernetes-staging.yml
rg --quiet --fixed-strings 'shared_alb_enabled' \
  .github/workflows/deploy-backend-staging.yml

ruby -ryaml -e '
  application = YAML.load_file(ARGV.fetch(0))
  labels = application.dig(
    "spec",
    "syncPolicy",
    "managedNamespaceMetadata",
    "labels"
  )
  abort("Argo CD must label the monitoring namespace for the staging ALB") unless
    labels == { "environment" => "staging" }

  values = YAML.load_file(ARGV.fetch(1))
  ingress = values.dig("grafana", "ingress")
  abort("Grafana HTTPS ingress must be enabled") unless ingress&.fetch("enabled", false)
  abort("Grafana ingress must use the staging ALB class") unless
    ingress["ingressClassName"] == "aero-staging-alb"
  abort("Grafana ingress hostname is incorrect") unless
    ingress["hosts"] == ["grafana-staging.aeroboundventures.com"]
  abort("Grafana must use its public HTTPS root URL") unless
    values.dig("grafana", "grafana.ini", "server", "root_url") ==
      "https://grafana-staging.aeroboundventures.com"
' gitops/staging/applications/monitoring.yaml helm/monitoring/values.yaml

if rg --quiet --fixed-strings 'bootstrap-required' gitops/staging; then
  echo "The staging desired state must reference a deployable image, not bootstrap-required." >&2
  exit 1
fi

ruby -ryaml -e '
  documents = YAML.load_stream(File.read(ARGV.fetch(0))).compact
  role = documents.find { |document| document["kind"] == "Role" }
  binding = documents.find { |document| document["kind"] == "RoleBinding" }

  abort("Deploy Role is missing") unless role
  abort("Deploy RoleBinding is missing") unless binding
  abort("Deploy Role must be namespace-scoped to argocd") unless
    role.dig("metadata", "namespace") == "argocd"

  rules = role.fetch("rules", [])
  abort("Deploy Role must contain exactly one rule") unless rules.length == 1
  application_rule = rules.first
  abort("Deploy Role must only target Argo CD Applications") unless
    application_rule.fetch("apiGroups", []) == ["argoproj.io"] &&
    application_rule.fetch("resources", []) == ["applications"]
  abort("Deploy Role may only grant get, list, and watch") unless
    application_rule.fetch("verbs", []).sort == %w[get list watch]

  deploy_group = binding.fetch("subjects", []).find do |subject|
    subject["kind"] == "Group" && subject["name"] == "aero-staging-deploy"
  end
  abort("Deploy RoleBinding must bind the aero-staging-deploy group") unless deploy_group
  abort("Deploy RoleBinding must only bind the deployment group") unless
    binding.fetch("subjects", []).length == 1
  abort("Deploy RoleBinding must reference the deploy Role") unless
    binding["roleRef"] == {
      "apiGroup" => "rbac.authorization.k8s.io",
      "kind" => "Role",
      "name" => "staging-deploy-argocd-reader"
    }
' gitops/bootstrap/deploy-role-rbac.yaml

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

monitoring_workspace="$(mktemp -d)"
trap 'rm -rf "${monitoring_workspace}"' EXIT
monitoring_chart="${monitoring_workspace}/chart"
monitoring_repository_config="${monitoring_workspace}/repositories.yaml"
monitoring_repository_cache="${monitoring_workspace}/repository-cache"
mkdir "${monitoring_chart}"
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts \
  --repository-config "${monitoring_repository_config}" \
  --repository-cache "${monitoring_repository_cache}"
helm repo add grafana-community https://grafana-community.github.io/helm-charts \
  --repository-config "${monitoring_repository_config}" \
  --repository-cache "${monitoring_repository_cache}"
cp helm/monitoring/Chart.yaml \
  helm/monitoring/Chart.lock \
  helm/monitoring/values.yaml \
  "${monitoring_chart}/"
helm dependency build "${monitoring_chart}" \
  --repository-config "${monitoring_repository_config}" \
  --repository-cache "${monitoring_repository_cache}"
helm lint "${monitoring_chart}"
helm template aero-monitoring "${monitoring_chart}" \
  --namespace monitoring >/dev/null

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
rg --quiet --fixed-strings 'gitops/bootstrap/deploy-role-rbac.yaml' \
  .github/workflows/terraform-kubernetes-staging.yml
rg --quiet --fixed-strings 'gitops/**' \
  .github/workflows/staging-backend.yml
rg --quiet --fixed-strings 'kubernetes_groups = ["aero-staging-deploy"]' \
  terraform/kubernetes-staging/github_actions.tf

if rg --quiet --fixed-strings \
  'resource "aws_eks_access_policy_association" "github_actions_argocd_view"' \
  terraform/kubernetes-staging/github_actions.tf; then
  echo "The ineffective EKS Argo CD view policy must not be configured." >&2
  exit 1
fi

rg --quiet --fixed-strings 'bootstrap-required' \
  .github/workflows/terraform-kubernetes-staging.yml
rg --quiet --fixed-strings -- \
  "--patch='{\"status\":{\"operationState\":{\"phase\":\"Terminating\"}}}'" \
  .github/workflows/terraform-kubernetes-staging.yml

if rg --quiet --fixed-strings -- "--patch='{\"operation\":null}'" \
  .github/workflows/terraform-kubernetes-staging.yml; then
  echo "Recovery must use Argo CD's Terminating operation phase." >&2
  exit 1
fi
rg --quiet --fixed-strings 'bash .github/scripts/validate-gitops.sh' \
  .github/workflows/staging-backend.yml
rg --quiet --fixed-strings 'sudo apt-get install --yes ripgrep' \
  .github/workflows/staging-backend.yml
rg --quiet --fixed-strings 'needs: validate' \
  .github/workflows/staging-backend.yml

ruby -ryaml -e '
  workflow = YAML.load_file(ARGV.fetch(0))
  steps = workflow.fetch("jobs").fetch("terraform").fetch("steps")
  bootstrap = steps.find { |step| step["name"] == "Bootstrap staging GitOps" }
  abort("GitOps bootstrap step is missing") unless bootstrap

  root_sync_wait = bootstrap.fetch("run").match?(
    %r{--for=jsonpath=.\{\.status\.sync\.status\}=Synced\s+\\?\s*application/aero-staging-root}
  )
  abort("Bootstrap must not wait for the root Application to become fully synced") if
    root_sync_wait
' .github/workflows/terraform-kubernetes-staging.yml

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

ruby -ryaml -e '
  workflow = YAML.load_file(ARGV.fetch(0))
  steps = workflow.fetch("jobs").fetch("deploy").fetch("steps")
  wait = steps.find { |step| step["name"] == "Wait for Argo CD reconciliation" }
  abort("Argo CD reconciliation step is missing") unless wait

  script = wait.fetch("run")
  reads = script.scan("get application/aero-staging-backend").length
  abort("Reconciliation must read the Application exactly once per attempt") unless reads == 1
  abort("Reconciliation must not suppress Application read failures") if
    script.include?("2>/dev/null") || script.include?("|| true")
  abort("Reconciliation must use a wall-clock deadline") unless
    script.include?("reconciliation_deadline=$((SECONDS + 600))")
  abort("Reconciliation must report every observed status") unless
    script.include?("sync=${sync_status} health=${health_status}")
' .github/workflows/deploy-backend-staging.yml

ruby -ryaml -e '
  workflow = YAML.load_file(ARGV.fetch(0))
  steps = workflow.fetch("jobs").fetch("terraform").fetch("steps")
  bootstrap = steps.find { |step| step["name"] == "Bootstrap staging GitOps" }
  abort("GitOps bootstrap step is missing") unless bootstrap

  script = bootstrap.fetch("run")
  abort("Bootstrap must wait for the monitoring Application") unless
    script.include?("--for=create application/aero-staging-monitoring")
  abort("Bootstrap must verify monitoring synchronization and health") unless
    script.include?(".status.sync.status}") && script.include?("=Synced") &&
      script.include?(".status.health.status}") && script.include?("=Healthy")
  abort("Bootstrap must verify that the Grafana Ingress receives an ALB hostname") unless
    script.include?("ingress/grafana") &&
      script.include?("status.loadBalancer.ingress[0].hostname") &&
      script.include?(%q(="${backend_alb_hostname}"))
' .github/workflows/terraform-kubernetes-staging.yml

echo "GitOps contract validation passed."
