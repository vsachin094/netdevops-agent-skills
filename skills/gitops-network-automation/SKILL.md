---
name: gitops-network-automation
description: "Implement GitOps workflows for network configuration using ArgoCD or Flux with Kustomize/Helm, automated sync, drift detection, and progressive delivery. Use this skill when network config must be declaratively managed from Git with automated reconciliation."
license: MIT
compatibility: Kubernetes 1.27+; ArgoCD 2.8+ or Flux 2.0+; Kustomize/Helm; Git repository; network operator/controller
---

# GitOps Network Automation (Advanced)

Treat network configuration as Kubernetes resources managed by GitOps controllers. The Git repository is the single source of truth; the cluster continuously reconciles actual state.

## Core Engineering Capabilities

- Define network resources as Kubernetes CRDs (NetworkDevice, NetworkConfig, BGP Peer, VLAN, Interface) managed by a network operator.
- Configure ArgoCD Applications or Flux Kustomizations with automated sync, prune, and self-heal.
- Implement progressive delivery with canary/blue-green for network changes using Argo Rollouts or Flagger.
- Build drift detection that alerts on divergence between Git and actual device state.
- Use Kustomize overlays for per-environment (dev/staging/prod) and per-site variations.

## Strict Engineering Guardrails (Anti-Hallucination & Best Practices)

- Never apply changes directly to devices outside GitOps; all mutations go through Git commit/PR.
- Use `server-side apply` with field ownership to prevent conflicts between operators and manual changes.
- Implement pre-sync hooks for pre-checks (reachability, capacity) and post-sync hooks for post-checks (adjacency, reachability).
- Require PR approval and status checks before merge; ArgoCD sync window controls when changes apply.
- Keep secrets in sealed-secrets, Vault, or External Secrets Operator; never in Git.
- Define sync windows and freeze periods; use `argocd.argoproj.io/sync-options: Validate=true` for dry-run.

## Step-by-Step Agent Execution Workflow

### Phase 1 (Intake & Scope)

Identify the network operator/controller, CRD schema, Git repository structure, environments, sync policies, and rollback procedures. Confirm which resources are managed vs. observed.

### Phase 2 (Implementation)

1. **CRD/Operator selection** — Choose or build operator (e.g., `network-operator`, `cnf-operator`, custom).
2. **Git repo structure** — `base/` + `overlays/{dev,staging,prod}/{site}/` with Kustomize.
3. **ArgoCD/Flux setup** — Applications/Kustomizations with sync policy, ignore differences, health checks.
4. **Pre/post sync hooks** — Jobs for reachability, config validation, adjacency checks.
4. **Drift alerting** — Prometheus rules on `argocd_app_sync_status` and custom drift metrics.

### Phase 3 (Verification)

Test PR workflow: change in Git → ArgoCD diff → sync → device verification → drift alert on manual change. Validate rollback via `argocd app rollback` and Git revert.

1. Commit config change to feature branch, open PR.
2. CI runs syntax check, unit tests, dry-run render.
3. Merge triggers ArgoCD sync; pre-sync hook validates preconditions.
4. Post-sync hook verifies device state; drift alert fires on manual change.

## Production Code / Template Example

### Input / Requirement

Provide network operator CRDs, Git repo layout, environments, sync policies, hook scripts, and drift alert thresholds.

### Output / Generated Code

Return Kustomize base/overlays, ArgoCD Application manifests, hook Job templates, and drift detection rules.

```yaml
# base/networkdevice.yaml
apiVersion: network.example.com/v1alpha1
kind: NetworkDevice
metadata:
  name: leaf-01
spec:
  managementIP: 192.0.2.11
  platform: eos
  credentialsRef:
    name: leaf-01-creds
  config:
    hostname: leaf-01
    interfaces:
      - name: Ethernet1
        description: "Uplink to spine"
        ipv4: 192.0.2.1/30
```

```yaml
# overlays/prod/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - ../../base
patches:
  - patch: |-
      - op: replace
        path: /spec/config/interfaces/0/description
        value: "PROD Uplink to spine"
    target:
      kind: NetworkDevice
```

```yaml
# argocd/application.yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: network-prod
  namespace: argocd
spec:
  project: network
  source:
    repoURL: https://git.example.com/network-config.git
    targetRevision: main
    path: overlays/prod
  destination:
    server: https://kubernetes.default.svc
    namespace: network-system
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
      allowEmpty: false
    syncOptions:
      - Validate=true
      - CreateNamespace=true
    retry:
      limit: 5
      backoff:
        duration: 5s
        factor: 2
        maxDuration: 3m
```

```yaml
# hooks/pre-sync-check.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: pre-sync-check
  annotations:
    argocd.argoproj.io/hook: PreSync
    argocd.argoproj.io/hook-delete-policy: HookSucceeded
spec:
  template:
    spec:
      restartPolicy: OnFailure
      containers:
        - name: check
          image: netops/precheck:latest
          env:
            - name: TARGET_DEVICES
              valueFrom:
                configMapKeyRef:
                  name: sync-targets
                  key: devices
          command: ["python", "/app/precheck.py"]
```

## Validation, Linting & Testing Commands

- `kustomize build overlays/prod` — validate overlays render correctly
- `argocd app diff network-prod` — preview changes before sync
- `kubeval` or `kubeconform` — validate rendered manifests
- Test drift: manually change device config → verify alert fires
- Test rollback: `argocd app rollback network-prod <revision>`
- Run `python3 scripts/validate_skills.py`.

## References

- [ArgoCD documentation](https://argo-cd.readthedocs.io/)
- [Flux documentation](https://fluxcd.io/)
- [Kustomize documentation](https://kustomize.io/)
- [GitOps principles](https://www.gitops.tech/)

## Offline Execution Contract

Generate Kustomize/ArgoCD manifests and hook templates locally. Without a cluster, validate YAML syntax and Kustomize rendering; do not claim sync, reconciliation, or drift detection behavior.

## Architecture & Technical Design Patterns

**Repository Structure:**
```
network-config/
├── base/
│   ├── networkdevice.yaml
│   ├── bgppeer.yaml
│   ├── vlan.yaml
│   └── kustomization.yaml
├── overlays/
│   ├── dev/
│   │   ├── site-a/
│   │   └── site-b/
│   ├── staging/
│   └── prod/
│       ├── site-a/
│       └── site-b/
├── hooks/
│   ├── pre-sync-check.yaml
│   └── post-sync-verify.yaml
└── argocd/
    ├── application-dev.yaml
    ├── application-staging.yaml
    └── application-prod.yaml
```

**Sync Policy Decision Matrix:**

| Environment | Automated Sync | Prune | Self-Heal | Sync Window |
|-------------|----------------|-------|-----------|-------------|
| dev | ✓ | ✓ | ✓ | Always |
| staging | ✓ | ✓ | ✓ | Business hours |
| prod | Manual | ✓ | ✓ | Change window only |

**Drift Detection:**
- ArgoCD `ComparisonError`/`Degraded` status → alert
- Custom controller metrics: `network_device_drift_total{device,field}`
- Periodic reconciliation job compares device running config vs. CRD spec

**Secrets Management:**
- `SealedSecret` for Git-encrypted secrets
- `ExternalSecret` pulling from Vault/AWS Secrets Manager
- Never store plaintext credentials in Git