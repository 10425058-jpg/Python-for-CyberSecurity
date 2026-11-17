# Deep Dive 16 — Cloud security, container isolation and DevSecOps using Python

> **Hands-on:** [Chapter 16 Guided Lab](../lab-manual/16-GUIDED-LAB.md) · [100 worked answers](../solutions/by-exercise/README.md). Run negative tests and document limitations.

**Level:** intermediate → advanced · **Estimated study:** 12–18 hours.

## Mission: audit a synthetic cloud inventory without any cloud account

You are given JSON records describing storage buckets, VM instances and workload identities. Your job is to create a **read-only policy report** on resources that violate an organization's configuration baseline. This teaches secure automation without changing production settings.

## 1. Shared responsibility and identity

Cloud providers secure underlying service infrastructure; customers must configure their own identities, networking, data access, application security and monitoring according to the specific service model. Responsibilities differ for IaaS, PaaS and SaaS, and vary by provider.

A cloud IAM policy defines **principal → action → resource → conditions**. A broad `*` permission can expose much more than intended. Use managed workload identities and short-lived scoped credentials where available, not long-lived keys embedded in scripts.

### Policy example
An approved inventory process may need:
- Read configurations for assets in a specific account/project.
- Read resource policy metadata but **not** object contents.
- Read audit configuration status but **not** production secrets.
- Emit findings to a protected reporting destination.
It should not have permission to delete, create or reconfigure resources.

## 2. Separate observation from remediation

A safe audit tool does not automatically "fix" a nonconforming resource. Automatically making a private bucket public or blocking a business-critical service can cause an incident even when the intention is defensive.

Design the flow:
```text
scoped read-only identity
   ↓
inventory API with pagination + timeouts
   ↓
validated resource schema
   ↓
pure policy evaluation
   ↓
finding with evidence and severity
   ↓
human approval / change management
   ↓
separate narrowly privileged remediation workflow
```

## 3. Pure policy evaluator example

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class StorageResource:
    resource_id: str
    encryption_enabled: bool
    public_access_blocked: bool

@dataclass(frozen=True)
class Finding:
    resource_id: str
    policy_id: str
    reason: str

def evaluate_storage(resource: StorageResource) -> list[Finding]:
    results = []
    if not resource.encryption_enabled:
        results.append(Finding(resource.resource_id,
                               "STORAGE-ENC-01", "encryption disabled"))
    if not resource.public_access_blocked:
        results.append(Finding(resource.resource_id,
                               "STORAGE-PUBLIC-02", "public access not blocked"))
    return results

lab = StorageResource("mock-storage-001", False, True)
assert len(evaluate_storage(lab)) == 1
```

The policy is **illustrative**. Encryption-at-rest and public access controls have provider-specific semantics; a single boolean from a synthetic record is not sufficient for real compliance validation.

### Why pure functions matter
`evaluate_storage` has no API credentials, network access or writes. You can test hundreds of cases in milliseconds. A separate adapter fetches live configuration *only in an authorized environment* and records the provider response and timestamp.

## 4. API realities: pagination, rate limits, consistency

A vendor API may return only 100 results per page, a pagination token, or partial failure. Real cloud inventories must:
- Enumerate all intended accounts/subscriptions/projects and regions.
- Use explicit scopes and correct pagination.
- Respect service rate limits and deadlines.
- Retry only safe queries with backoff and global budget.
- Handle eventual consistency and deleted/updated resources.
- Record "inventory incomplete" when some calls fail.
- Avoid reporting "no issues" after an error.

Incorrect pagination is a common reason compliance reports are falsely reassuring.

## 5. Containers are not automatically sandboxes

Containers isolate processes with OS mechanisms such as namespaces and cgroups, while sharing important host resources (especially the kernel on Linux). Container security depends on:
- Running as a non-root user when feasible.
- Dropping unnecessary Linux capabilities.
- Avoiding privileged mode and unrestricted host mounts.
- Read-only filesystems where possible.
- Limiting CPU/memory and filesystem writes.
- Seccomp, SELinux/AppArmor and runtime policies.
- Image provenance, patching and controlled registries.
- Secrets via workload identity/approved secret services.
- Strong Kubernetes RBAC and network policy.

Mounting `/var/run/docker.sock` inside a container can allow extensive control of the host's Docker daemon. It is not a harmless convenience.

## 6. Kubernetes security concepts

Pods, deployments, namespaces, service accounts, RBAC, network policies, admission controls, secrets, volume mounts, image policies, resource requests/limits and audit logs. A Kubernetes *namespace* provides organization and some isolation boundaries, not a stand-alone tenant security boundary. Review workload permissions and network access separately.

### Example checklist for a Pod
1. Is it privileged?
2. Does it use hostPath, hostPID, hostNetwork or hostIPC?
3. What user/group does it run as?
4. Are extra capabilities granted?
5. Is the root filesystem writable?
6. Are secrets injected too broadly?
7. Which service account token is mounted?
8. Are egress destinations constrained?
9. Is the image maintained and pinned appropriately?
10. Are requests/limits and admission policies defined?

## 7. Secure CI/CD using Python tooling

The CI pipeline is itself a powerful identity. It may deploy software, read secrets, build artifacts and alter repository content. Threats include untrusted PR scripts, compromised actions, poisoned cache, stolen tokens and dependency confusion.

A layered pipeline:
- Formatter/linter (`ruff`).
- Static typing (`mypy` or pyright).
- Unit and integration tests.
- Security analysis (`bandit`/Semgrep) with human triage.
- Dependency advisory scanning (`pip-audit`).
- Secret scanning and SBOM.
- Pinned, reviewed action dependencies and least-privilege token permissions.
- Artifact provenance/signatures and controlled deployment identity.

Do not expose production secrets to test jobs executing untrusted contributions. Passing a scanner is not proof of a secure release.

## 8. Supply-chain threat modeling

Even a library with no listed CVEs may be malicious or abandoned. Review package publisher identity, release provenance, typosquatting risks, build backend behavior, transitive dependencies, licenses and update practices. Use locked, reproducible environments and staged upgrades where practical.

## 9. Lab: policy-as-code with mock resources
1. Create three synthetic storage resource objects: compliant, unencrypted, and public-access-not-blocked.
2. Implement `evaluate_storage` and assert its outputs.
3. Define a JSON schema for inventory records; reject missing/wrong type fields.
4. Write a JSONL finding report with policy ID, resource ID, timestamp and source.
5. Add an "incomplete inventory" scenario; do not claim compliance if one page failed.
6. Write a remediation proposal *without applying changes*.
7. Document what would be needed to replace mocks with read-only vendor SDKs (IAM role, scope, pagination, SDK versions, auditing).

## 10. Questions and checks
**Q:** What is a role's "read-only" scope? **A:** Specific actions and resource patterns; broad read can still expose sensitive content, so inventory roles must be narrow.

**Q:** Why is container root risky? **A:** Increased privileges inside a runtime that may interact with the host; risk depends on isolation and mounts/capabilities.

**Q:** Can a Python `venv` safely run malicious dependencies? **A:** No, it is a dependency isolation environment, not a hostile-code sandbox.

**Q:** Why are failed API pages a security reporting problem? **A:** They can falsely make missing assets appear compliant.

**Q:** Why separate remediation? **A:** Changes need explicit authority, change control, rollback and independent review.

**References:** [Kubernetes security](https://kubernetes.io/docs/concepts/security/), [OWASP CI/CD risks](https://owasp.org/www-project-top-10-ci-cd-security-risks/), [Python Packaging](https://packaging.python.org/).


## 11. Case study: a mock cloud posture audit with explainable findings

The phrase "read-only cloud audit" is easy to misuse: read permissions may still reveal confidential object contents or secrets. For a compliance inventory, scope **which configuration fields** are needed and avoid broad data read access.

### Pure, offline policy evaluator

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class Storage:
    account: str
    resource_id: str
    encryption: bool
    public_access_blocked: bool

@dataclass(frozen=True)
class PolicyFinding:
    account: str
    resource_id: str
    control: str
    reason: str

def audit_storage(record: Storage) -> list[PolicyFinding]:
    findings = []
    if not record.encryption:
        findings.append(PolicyFinding(
            record.account, record.resource_id,
            "STORAGE-ENC-01", "encryption policy not met"
        ))
    if not record.public_access_blocked:
        findings.append(PolicyFinding(
            record.account, record.resource_id,
            "STORAGE-PUBLIC-01", "public access policy not met"
        ))
    return findings

test = Storage("toy-account","asset-01",False,True)
assert len(audit_storage(test)) == 1
```

This example assumes validated typed records. In a real cloud, settings are provider-specific and might involve inheritance, organization policies, effective access, encryption keys and exceptions. A boolean check cannot fully determine compliance.

### Fault injection: a missing inventory page

Suppose an API returns pages 1–5 but page 4 times out. If your tool reports "all assets compliant" based on pages 1–3 and 5, it has created an unsafe false all-clear. Model the batch with a completeness status:

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class InventoryResult:
    records: tuple[Storage, ...]
    pages_expected: int
    pages_received: int

    @property
    def complete(self) -> bool:
        return (
            self.pages_expected >= 0
            and self.pages_received == self.pages_expected
        )

result = InventoryResult((test,), 5, 4)
assert not result.complete
```

A complete API inventory may not expose total pages in advance; production software must follow provider-specific continuation tokens and report errors rather than assuming pagination is finished.

## 12. Container execution and supply-chain trust boundaries

| Boundary | Risk | Example control |
|---|---|---|
| Image registry → build | compromised/tag-swapped image | approved registry, immutable digests, provenance |
| CI job → secrets | PR reads deployment credential | separate untrusted PR runners and scoped identities |
| Container → host | privileged mode, host mounts, Docker socket | rootless where feasible, no sensitive host mounts |
| Pod → cluster API | overbroad service-account token | scoped Kubernetes RBAC |
| Pod → Internet/metadata | unintended exfiltration | egress/network policies and workload identity |
| Library install → runtime | typosquatting, unsafe build backend | reviewed locked dependencies and isolation |

### Why `pip install` is an execution boundary
Python packages may execute build hooks during installation and code during import. A virtual environment makes package management cleaner but does **not** prevent malicious code from reading your user's files. Evaluate dependencies, pin verified releases and restrict CI credentials during build/test.

## 13. A human-reviewed remediation flow

Even a perfect policy finding does not grant permission to change infrastructure. Use:
1. Inventory and evidence.
2. Policy validation and false-positive review.
3. Impact analysis and change owner.
4. Approved maintenance window and rollback.
5. Minimal write identity separate from inventory role.
6. Re-scan after change, verifying actual effective settings.
7. Audit the action and close with evidence.

This separation protects availability while enabling defensible compliance.

## 14. Exercises and expected answers

**A:** Implement an audit of three synthetic storage records; return one or more `PolicyFinding` objects and test rule IDs.

**B:** Simulate incomplete pagination. A correct report states "inventory incomplete", never "all compliant".

**C:** Review a mock Kubernetes pod with privileged mode, hostPath mount and writable root filesystem. Explain three distinct risks and safer defaults.

**D:** Threat-model a workflow executing untrusted PR code. Why does `permissions: contents: read` help but not protect secrets deliberately passed to the job? The job still has access to anything in its environment.

**E:** Propose scoped cloud IAM permissions for reading only configuration metadata. Justify every permission and identify data you deliberately cannot read.

**F:** Explain why a production cloud posture audit must inspect **effective** security state, not just one provider's displayed boolean.

**References:** [OWASP CI/CD Security](https://owasp.org/www-project-top-10-ci-cd-security-risks/), [Kubernetes security](https://kubernetes.io/docs/concepts/security/).
