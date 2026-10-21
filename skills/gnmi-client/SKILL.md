---
name: gnmi-client
description: "Build programmatic gNMI clients in Python or Go for Get, Set, Subscribe (ON_CHANGE/SAMPLE/TARGET_DEFINED) with TLS/mTLS, path encoding, and typed responses. Use this skill when automation needs direct gNMI access to network devices for config, state, or streaming telemetry."
license: MIT
compatibility: Python 3.10+ with gnmi-proto, grpcio; or Go 1.21+ with gnmi-go; OpenConfig gNMI spec; device gNMI endpoint with TLS certs
---

# gNMI Client (Advanced)

Direct gNMI access for config, operational state, and streaming telemetry. Prefer this over SSH/CLI when the device supports gNMI and you need structured, typed data with transaction semantics.

## Core Engineering Capabilities

- **Get** — Retrieve config/state with typed Path prefixes, JSON_IETF/JSON/ASCII/Proto encoding, and pagination.
- **Set** — Update, replace, delete config with transaction semantics (atomic or best-effort), validate-only dry-run.
- **Subscribe** — Stream telemetry: ON_CHANGE, SAMPLE, TARGET_DEFINED with heartbeat, sync_response, and per-path sample intervals.
- **Capabilities** — Negotiate supported models, encodings, gNMI version; cache for session reuse.
- **TLS/mTLS** — Client cert auth, CA verification, hostname override for lab; fallback to insecure for testing only.

## Strict Engineering Guardrails (Anti-Hallucination & Best Practices)

- **Use Path objects, not raw strings** — Build `gnmi.Path` with `elem` list; encode keys as map. Avoid string concatenation for paths.
- **Set timeouts on every RPC** — Default 10s connect, 30s read; Set may need 60s+ for large commits.
- **Handle `NOT_FOUND` vs `PERMISSION_DENIED`** — Distinguish missing path from auth; retry only transient gRPC codes (UNAVAILABLE, DEADLINE_EXCEEDED).
- **Set: prefer `REPLACE` for atomic, `UPDATE` for merge** — Use `validate_only=true` for dry-run; check `response.prefix` for errors.
- **Subscribe: bound memory** — Use bounded channel/queue; drop or backpressure on slow consumer; track sync_response for alignment.
- **mTLS required for production** — Store client cert/key in secret manager; verify server cert; never disable verify in prod.
- **Path encoding** — Prefer JSON_IETF for readability; Proto for performance. Decode `TypedValue` to native types (int, bool, string, bytes).

## Step-by-Step Agent Execution Workflow

### Phase 1 (Intake & Scope)

Identify target device gNMI endpoint, TLS certs, required paths (config/state/telemetry), encoding, and whether Get/Set/Subscribe needed. Confirm device gNMI version and supported models via Capabilities.

### Phase 2 (Implementation)

1. **Client factory** — Create gRPC channel with TLS creds, interceptors for retries/metadata, health check.
2. **Capabilities** — Call once per session; cache model list, supported encodings, gNMI version.
3. **Get** — Build `GetRequest` with Path list, encoding, type (CONFIG/STATE/OPERATIONAL); parse `Notification` → typed dict.
3. **Set** — Build `SetRequest` with Update/Replace/Delete; use `validate_only` for dry-run; parse `SetResponse` for errors.
4. **Subscribe** — Build `SubscribeRequest` with SubscriptionList; handle stream: sync_response, updates, heartbeats; decode `TypedValue`.
5. **Path helpers** — Functions to build Path from string (xpath-style) or components; encode keys.

### Phase 3 (Verification)

Test against device or gNMI simulator (gnmi_target, gnmi-spec): Capabilities, Get valid path, Get invalid path, Set validate_only, Set commit, Subscribe ON_CHANGE/SAMPLE, TLS auth, cert rotation, reconnection, large payload pagination.

1. Run Capabilities; log supported models/encodings.
2. Get known path; assert typed response matches expected schema.
3. Set validate_only on valid/invalid config; assert error codes.
4. Subscribe to counter path; verify sample arrives within interval.
5. Test cert rotation: reload client creds without restart.

## Production Code / Template Example

### Input / Requirement

Provide gNMI target (host:port), TLS cert paths or insecure flag, paths to Get/Set/Subscribe, encoding, timeout, and expected response schema.

### Output / Generated Code

Return client module with Get/Set/Subscribe methods, typed response models, TLS config, and test suite.

```python
# gnmi_client.py
from __future__ import annotations
import grpc
from dataclasses import dataclass
from typing import Any, Iterator, Optional
from gnmi import gnmi_pb2, gnmi_pb2_grpc

@dataclass
class GnmiTarget:
    host: str
    port: int = 57400
    ca_cert: Optional[str] = None
    client_cert: Optional[str] = None
    client_key: Optional[str] = None
    insecure: bool = False
    target_name: Optional[str] = None

@dataclass
class GnmiGetResult:
    path: str
    value: Any
    timestamp: int
    path_prefix: str = ""

class GnmiClient:
    def __init__(self, target: GnmiTarget, timeout: float = 30.0):
        self.target = target
        self.timeout = timeout
        self._channel: Optional[grpc.Channel] = None
        self._stub: Optional[gnmi_pb2_grpc.gNMIStub] = None
        self._capabilities: Optional[gnmi_pb2.CapabilityResponse] = None

    def _create_channel(self) -> grpc.Channel:
        if self.target.insecure:
            creds = grpc.local_channel_credentials()
        else:
            ca = open(self.target.ca_cert, "rb").read() if self.target.ca_cert else None
            cert = open(self.target.client_cert, "rb").read() if self.target.client_cert else None
            key = open(self.target.client_key, "rb").read() if self.target.client_key else None
            creds = grpc.ssl_channel_credentials(root_certificates=ca, private_key=key, certificate_chain=cert)
        return grpc.secure_channel(f"{self.target.host}:{self.target.port}", creds)

    def __enter__(self):
        self._channel = self._create_channel()
        self._stub = gnmi_pb2_grpc.gNMIStub(self._channel)
        return self

    def __exit__(self, *args):
        if self._channel:
            self._channel.close()

    def capabilities(self) -> gnmi_pb2.CapabilityResponse:
        if not self._capabilities:
            self._capabilities = self._stub.Capabilities(gnmi_pb2.CapabilityRequest(), timeout=self.timeout)
        return self._capabilities

    def get(self, paths: list[str], encoding: str = "JSON_IETF", datatype: str = "CONFIG") -> list[GnmiGetResult]:
        gnmi_paths = [self._parse_path(p) for p in paths]
        req = gnmi_pb2.GetRequest(
            path=gnmi_paths,
            type=getattr(gnmi_pb2.GetRequest.DataType, datatype),
            encoding=getattr(gnmi_pb2.Encoding, encoding),
        )
        resp = self._stub.Get(req, timeout=self.timeout)
        return [self._parse_notification(n) for n in resp.notification]

    def set(self, updates: list[tuple[str, Any]], replaces: list[tuple[str, Any]] = None, deletes: list[str] = None, validate_only: bool = False) -> gnmi_pb2.SetResponse:
        def mk_update(path, val):
            return gnmi_pb2.Update(path=self._parse_path(path), val=self._to_typed_value(val))
        req = gnmi_pb2.SetRequest(
            prefix=gnmi_pb2.Path(target=self.target.target_name) if self.target.target_name else None,
            update=[mk_update(p, v) for p, v in (updates or [])],
            replace=[mk_update(p, v) for p, v in (replaces or [])],
            delete=[self._parse_path(p) for p in (deletes or [])],
            validate_only=validate_only,
        )
        return self._stub.Set(req, timeout=self.timeout * 2)

    def subscribe(self, paths: list[str], mode: str = "SAMPLE", sample_interval: int = 10_000_000_000, encoding: str = "JSON_IETF") -> Iterator[GnmiGetResult]:
        subs = [gnmi_pb2.Subscription(
            path=self._parse_path(p),
            mode=getattr(gnmi_pb2.SubscriptionMode, mode),
            sample_interval=sample_interval,
        ) for p in paths]
        req = gnmi_pb2.SubscribeRequest(
            subscribe=gnmi_pb2.SubscriptionList(
                subscription=subs,
                mode="STREAM",
                encoding=getattr(gnmi_pb2.Encoding, encoding),
            )
        )
        for resp in self._stub.Subscribe(iter([req]), timeout=self.timeout):
            if resp.sync_response:
                continue
            for upd in resp.update:
                yield from self._parse_notification(upd)

    def _parse_path(self, path_str: str) -> gnmi_pb2.Path:
        # Simple xpath-style parser: /interfaces/interface[name=eth0]/state/counters
        elems = []
        for seg in path_str.strip("/").split("/"):
            if "[" in seg:
                name, rest = seg.split("[", 1)
                keys = {}
                for kv in rest.rstrip("]").split(","):
                    k, v = kv.split("=")
                    keys[k] = v.strip("'\"")
                elems.append(gnmi_pb2.PathElem(name=name, key=keys))
            else:
                elems.append(gnmi_pb2.PathElem(name=seg))
        return gnmi_pb2.Path(elem=elems, target=self.target.target_name)

    def _to_typed_value(self, val: Any) -> gnmi_pb2.TypedValue:
        if isinstance(val, bool): return gnmi_pb2.TypedValue(bool_val=val)
        if isinstance(val, int): return gnmi_pb2.TypedValue(int_val=val)
        if isinstance(val, float): return gnmi_pb2.TypedValue(float_val=val)
        if isinstance(val, str): return gnmi_pb2.TypedValue(string_val=val)
        if isinstance(val, bytes): return gnmi_pb2.TypedValue(bytes_val=val)
        if isinstance(val, dict): return gnmi_pb2.TypedValue(json_ietf_val=json.dumps(val).encode())
        raise ValueError(f"Unsupported value type: {type(val)}")

    def _parse_notification(self, notif: gnmi_pb2.Notification) -> list[GnmiGetResult]:
        results = []
        prefix = "".join(f"/{e.name}" for e in notif.prefix.elem) if notif.prefix.elem else ""
        for upd in notif.update:
            path = prefix + "".join(f"/{e.name}" for e in upd.path.elem)
            val = self._decode_typed_value(upd.val)
            results.append(GnmiGetResult(path=path, value=val, timestamp=notif.timestamp, path_prefix=prefix))
        return results

    def _decode_typed_value(self, tv: gnmi_pb2.TypedValue) -> Any:
        which = tv.WhichOneof("value")
        if which == "bool_val": return tv.bool_val
        if which == "int_val": return tv.int_val
        if which == "uint_val": return tv.uint_val
        if which == "float_val": return tv.float_val
        if which == "string_val": return tv.string_val
        if which == "bytes_val": return tv.bytes_val
        if which == "json_ietf_val": return json.loads(tv.json_ietf_val)
        if which == "json_val": return json.loads(tv.json_val)
        if which == "ascii_val": return tv.ascii_val
        if which == "proto_bytes": return tv.proto_bytes
        return None
```

```go
// gnmi_client.go
package gnmi

import (
    "context"
    "crypto/tls"
    "crypto/x509"
    "encoding/json"
    "fmt"
    "io/ioutil"
    "time"

    "github.com/openconfig/gnmi/proto/gnmi"
    "google.golang.org/grpc"
    "google.golang.org/grpc/credentials"
)

type Target struct {
    Host       string
    Port       int
    CaCert     string
    ClientCert string
    ClientKey  string
    Insecure   bool
    TargetName string
}

type Client struct {
    target    Target
    conn      *grpc.ClientConn
    client    gnmi.GNMIClient
    timeout   time.Duration
}

func NewClient(target Target, timeout time.Duration) (*Client, error) {
    var opts []grpc.DialOption
    if target.Insecure {
        opts = append(opts, grpc.WithTransportCredentials(insecure.NewCredentials()))
    } else {
        cert, err := tls.LoadX509KeyPair(target.ClientCert, target.ClientKey)
        if err != nil {
            return nil, err
        }
        caCert, err := ioutil.ReadFile(target.CaCert)
        if err != nil {
            return nil, err
        }
        caPool := x509.NewCertPool()
        caPool.AppendCertsFromPEM(caCert)
        tlsConfig := &tls.Config{
            Certificates:       []tls.Certificate{cert},
            RootCAs:            caPool,
            ServerName:         target.Host,
            InsecureSkipVerify: false,
        }
        opts = append(opts, grpc.WithTransportCredentials(credentials.NewTLS(tlsConfig)))
    }
    conn, err := grpc.Dial(fmt.Sprintf("%s:%d", target.Host, target.Port), opts...)
    if err != nil {
        return nil, err
    }
    return &Client{
        target:  target,
        conn:    conn,
        client:  gnmi.NewGNMIClient(conn),
        timeout: timeout,
    }, nil
}

func (c *Client) Close() error {
    return c.conn.Close()
}

func (c *Client) Get(ctx context.Context, paths []string, encoding gnmi.Encoding, datatype gnmi.GetRequest_DataType) ([]*gnmi.Notification, error) {
    gnmiPaths := make([]*gnmi.Path, len(paths))
    for i, p := range paths {
        gnmiPaths[i] = ParsePath(p, c.target.TargetName)
    }
    req := &gnmi.GetRequest{
        Path:      gnmiPaths,
        Type:      datatype,
        Encoding:  encoding,
    }
    resp, err := c.client.Get(ctx, req)
    if err != nil {
        return nil, err
    }
    return resp.Notification, nil
}

func (c *Client) Set(ctx context.Context, updates map[string]interface{}, validateOnly bool) (*gnmi.SetResponse, error) {
    var gnmiUpdates []*gnmi.Update
    for path, val := range updates {
        gnmiUpdates = append(gnmiUpdates, &gnmi.Update{
            Path: ParsePath(path, c.target.TargetName),
            Val:  ToTypedValue(val),
        })
    }
    req := &gnmi.SetRequest{
        Prefix:       &gnmi.Path{Target: c.target.TargetName},
        Update:       gnmiUpdates,
        ValidateOnly: validateOnly,
    }
    return c.client.Set(ctx, req)
}

func (c *Client) Subscribe(ctx context.Context, paths []string, mode gnmi.SubscriptionMode, sampleInterval uint64, encoding gnmi.Encoding) (gnmi.GNMI_SubscribeClient, error) {
    subs := make([]*gnmi.Subscription, len(paths))
    for i, p := range paths {
        subs[i] = &gnmi.Subscription{
            Path:            ParsePath(p, c.target.TargetName),
            Mode:            mode,
            SampleInterval:  sampleInterval,
        }
    }
    req := &gnmi.SubscribeRequest{
        Request: &gnmi.SubscribeRequest_Subscribe{
            Subscribe: &gnmi.SubscriptionList{
                Subscription: subs,
                Mode:         gnmi.SubscriptionList_STREAM,
                Encoding:     encoding,
            },
        },
    }
    return c.client.Subscribe(ctx)
}

// Helpers: ParsePath, ToTypedValue, DecodeTypedValue omitted for brevity
```

## Validation, Linting & Testing Commands

- **Python:** `pytest tests/ -v` (unit + gnmi_target simulator), `mypy gnmi_client.py`, `ruff check gnmi_client.py`
- **Go:** `go test ./... -v`, `go vet ./...`, `golangci-lint run`
- **Integration:** Run against gnmi_target simulator or lab device (SR Linux, IOS-XR, EOS gNMI)
- **Test cases:** Capabilities, Get valid/invalid path, Set validate_only/commit, Subscribe ON_CHANGE/SAMPLE, TLS/mTLS, reconnect, large payload

## References

- [gNMI Specification](https://github.com/openconfig/reference/blob/master/rpc/gnmi/gnmi-specification.md)
- [gnmi-proto Python](https://github.com/google/gnmi-proto)
- [gnmi-go](https://github.com/openconfig/gnmi-go)
- [gNMI Tools (gnmic)](https://github.com/karimra/gnmic)

## Offline Execution Contract

Generate client code and test against gnmi_target simulator or saved protobuf fixtures. Without device/gNMI endpoint, validate proto compilation, path parsing, typed value encoding/decoding; mark live gNMI behavior as unverified.

## Architecture & Technical Design Patterns

**Path Construction:**
```python
# Preferred: programmatic Path construction
path = gnmi.Path(elem=[
    gnmi.PathElem(name="interfaces"),
    gnmi.PathElem(name="interface", key={"name": "Ethernet1"}),
    gnmi.PathElem(name="state"),
    gnmi.PathElem(name="counters"),
])
```

**Encoding Choice:**
| Encoding | Use Case |
|----------|----------|
| JSON_IETF | Human-readable, debugging, config |
| JSON | Legacy, non-IETF models |
| PROTO | High-performance streaming, internal tools |
| ASCII | Legacy CLI-like output |

**Subscription Modes:**
- `SAMPLE` — periodic counter/state streaming (counters, interfaces)
- `ON_CHANGE` — event-driven (BGP peer state, interface up/down, config change)
- `TARGET_DEFINED` — device chooses (often ON_CHANGE for state, SAMPLE for counters)

**Set Transaction Semantics:**
- `UPDATE` — merge (like `load merge`)
- `REPLACE` — replace entire subtree (like `load replace`)
- `DELETE` — remove
- `validate_only=true` — dry-run, no commit

**Error Handling:**
```python
# gRPC status codes to handle
UNAVAILABLE -> retry with backoff
DEADLINE_EXCEEDED -> increase timeout, retry
PERMISSION_DENIED -> authz error, no retry
NOT_FOUND -> path/model not supported
INVALID_ARGUMENT -> malformed path/value
```

**Related Skills:**

- [gnmi-snmp-telemetry](gnmi-snmp-telemetry.md) — Telemetry collection config using gnmic
- [network-observability-stack](network-observability-stack.md) — Prometheus/Grafana stack consuming gNMI
- [network-testing-framework](network-testing-framework.md) — Test gNMI client in CI
- [containerlab-topologies](containerlab-topologies.md) — Lab devices with gNMI enabled
- [network-config-drift-detection](network-config-drift-detection.md) — Drift detection via gNMI Get