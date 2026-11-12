---
name: k8s-network-policy
description: "[Tier: Intermediate] Write Kubernetes CNI NetworkPolicy YAML, lint it offline, apply it with kubectl, and verify pod-to-pod connectivity before and after. Use this skill when a team needs declarative, versioned network segmentation inside a cluster instead of permissive default allow-all traffic."
license: MIT
compatibility: Kubernetes 1.21+ with the NetworkPolicy API enabled; a CNI that supports NetworkPolicy (Calico, Cilium, Antrea, Azure CNI); kubectl; optional kubeconftest/conftest/OPA for lint; kind or k3s lab cluster
---

# Kubernetes Network Policy (Intermediate)

Write, validate, and apply Kubernetes NetworkPolicy resources so pod traffic is denied by default and only allowed where explicitly required. Verify connectivity before and after each change, and keep a rollback path ready.

## Core Engineering Capabilities

- Write NetworkPolicy YAML for namespace isolation, podSelector, namespaceSelector, ingress/egress rules, named ports, IPBlock rules, and deny-by-default baselines.
- Deny all ingress and egress by default per namespace, then add only the allow rules the service graph requires.
- Split policies by concern: deny-by-default baseline, DNS/metrics allow, frontend-to-backend, application-to-database, and controlled egress.
- Lint policies offline with kubeconftest/conftest/OPA before touching the cluster, then run `kubectl --dry-run=client` to catch schema errors.
- Apply with `kubectl apply`, watch pod readiness and events, then run postcheck connectivity between allowed and denied pod pairs.
- Keep the previous Git revision handy so you can revert immediately if postchecks fail.
- Scope egress tightly: allow cluster DNS, NTP, and metrics only where needed; block cloud metadata unless a workload genuinely requires it.

## Architecture & Technical Design Patterns

```
service graph + namespace + label map
                  │
                  ▼
        NetworkPolicy YAML (one per concern)
                  │
                  ▼
       offline lint → kubectl --dry-run=client
                  │
                  ▼
            kubectl apply (one tier at a time)
                  │
                  ▼
     postcheck: curl/nc between allowed + denied pairs
                  │
                  ▼
        rollback gate: git revert on connectivity regression
```

Write one file per policy (for example `deny-all-default.yaml`, `allow-dns.yaml`, `allow-frontend-to-backend.yaml`) so each change is reviewable and reversible. Use named ports instead of bare numbers so a service port change does not break the policy. Use `namespaceSelector` for cross-namespace traffic and `podSelector` for same-namespace traffic. Avoid broad `ipBlock` egress unless an egress gateway or firewall logs the denied traffic.

## Strict Engineering Guardrails (Anti-Hallucination & Best Practices)

- Do not assume every CNI enforces NetworkPolicy the same way. Calico, Cilium, Antrea, and Azure CNI differ in denied-flow logging, `ipBlock` support, and egress behavior. Test against the CNI actually running in your cluster.
- An empty `ingress: []` in Kubernetes means "allow all ingress," not "deny all." Pair a deny-by-default policy with a `podSelector` that matches the real workloads, and confirm the CNI honors it before trusting it.
- Do not hardcode cluster IPs, pod CIDRs, service CIDRs, or cloud metadata addresses as universal constants. Treat them as examples that need deployment-specific values.
- Keep egress rules narrow. Allowing `0.0.0.0/0` in `ipBlock` removes segmentation and is a common audit finding.
- Confirm DNS (CoreDNS/kube-dns), admission webhooks, and metrics endpoints stay reachable after you apply deny-by-default, or workloads and control-plane components will break.
- Treat `kubectl apply` as a mutation: dry-run first, save the previous revision, and define the rollback trigger before you apply to shared or production namespaces.

## Step-by-Step Agent Execution Workflow

### Phase 1 (Intake & Scope)

Collect: cluster name and CNI type, namespaces, pod labels and selectors, the service graph (which pods talk to which), required ports and protocols, external egress needs, whether deny-by-default is required, the rollback trigger, and which hosts you will use for verification. Confirm the CNI enforces NetworkPolicy and which features it supports before you write any YAML.

### Phase 2 (Implementation)

Write the deny-by-default baseline first, then add allow rules one tier at a time. Run offline lint, then `kubectl --dry-run=client`. Apply one tier at a time starting in a non-production namespace, then move to production only after postchecks pass there.

### Phase 3 (Verification)

Run postcheck connectivity between expected-allowed pod pairs (should succeed) and expected-denied pairs (should fail). Confirm DNS and metrics reachability. On any regression, revert to the previous Git revision and re-verify. Document the final policy set and any CNI-specific behavior you observed.

### Input / Requirement

A cluster with a NetworkPolicy-enabled CNI; namespaces, pod selectors, service dependencies, ports and protocols, and egress requirements.

### Output / Generated Code

Versioned NetworkPolicy YAML files, a verification command list, and a rollback plan that references the previous Git revision.

```python
# Create a deny-by-default NetworkPolicy using the Kubernetes Python client.
# Values are illustrative; replace namespace, labels, and ports before use.
from kubernetes import client, config

def create_deny_by_default(namespace: str, name: str = "deny-all-default") -> client.V1NetworkPolicy:
    body = client.V1NetworkPolicy(
        api_version="networking.k8s.io/v1",
        kind="NetworkPolicy",
        metadata=client.V1ObjectMeta(name=name, namespace=namespace),
        spec=client.V1NetworkPolicySpec(
            pod_selector=client.V1LabelSelector(match_labels={}),
            policy_types=["Ingress", "Egress"],
        ),
    )
    return body

# Example usage (illustrative; requires kubeconfig or in-cluster config)
# config.load_kube_config()
# netapi = client.NetworkingV1Api()
# policy = create_deny_by_default("production")
# netapi.create_namespaced_network_policy(namespace="production", body=policy)
```
## Production Code / Template Example

```yaml
# deny-all-default for the production namespace.
# Replace `production` with your real namespace before applying.
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-all-default
  namespace: production
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
---
# allow cluster DNS to production workloads.
# Replace `production` and `app: coredns` with your real values.
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-dns
  namespace: production
spec:
  podSelector:
    matchLabels:
      app: coredns
  policyTypes:
  - Ingress
  ingress:
  - from:
    - namespaceSelector: {}
    ports:
    - protocol: UDP
      port: 53
    - protocol: TCP
      port: 53
---
# allow frontend to backend on port 8080.
# Replace namespace and labels with your real values.
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-frontend-to-backend
  namespace: production
spec:
  podSelector:
    matchLabels:
      app: backend
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: frontend
    ports:
    - protocol: TCP
      port: 8080
```

## Validation, Linting & Testing Commands

- `kubectl --dry-run=client -f deny-all-default.yaml` — catch schema errors without mutating the cluster.
- `kubectl --dry-run=client -f allow-dns.yaml -f allow-frontend-to-backend.yaml` — dry-run multiple files at once.
- `kubeconftest` or `conftest` or `opa test` against your policy directory — offline semantic lint before apply.
- `kubectl apply -f deny-all-default.yaml --dry-run=client -o yaml` — inspect rendered resources before applying.
- Postcheck allowed pair: `kubectl exec <frontend-pod> -- curl -v <backend-service>:8080`
- Postcheck denied pair: `kubectl exec <unrelated-pod> -- nc -zv <backend-service> 8080` (should fail)
- DNS check: `kubectl exec <pod> -- nslookup kubernetes.default.svc.cluster.local`
- Rollback: `git revert <policy-commit> && kubectl apply -f deny-all-default.yaml`
- Run `python3 scripts/validate_skills.py` from the repository root.

## References

- [Kubernetes NetworkPolicy documentation](https://kubernetes.io/docs/concepts/services-networking/network-policies/)
- [Calico network policy](https://docs.tigera.io/calico/latest/networking/kubernetes-network-policy/)
- [Cilium network policy](https://docs.cilium.io/en/stable/security/policy/)
- [kubectl apply dry-run](https://kubernetes.io/docs/tasks/manage-kubernetes-objects/declarative-config/#dry-run)
- [kind local clusters](https://kind.sigs.k8s.io/) / [k3s](https://k3s.io/)

## Offline Execution Contract

Authoring, offline lint, and dry-run work without a cluster. `kubectl apply` and postcheck connectivity require a cluster (kind/k3s or a lab). CNI-specific deny-flow logging and egress behavior must be verified against the target cluster's CNI and version; mark unverified until tested there.

## Related Skills

- [netbox-nautobot-api](../netbox-nautobot-api/SKILL.md) — source of truth for service and IP inventory that feeds policy rules
- [network-rest-clients](../network-rest-clients/SKILL.md) — typed clients for Kubernetes API and CNI controllers
- [network-config-drift-detection](../network-config-drift-detection/SKILL.md) — detect drift from the approved policy baseline
