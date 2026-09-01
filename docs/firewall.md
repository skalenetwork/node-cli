# Node firewall

node-cli manages the host firewall with nftables. It owns the base chain
`inet firewall skale` (hook `input`, priority 1), while skale-admin dynamically
manages one base chain per sChain (`skale-<name>`, priority 0) in the same
table with per-peer accept rules and a terminal drop for the sChain port range.

Since a packet traverses **every** base chain on a hook (only `drop` is
terminal, `accept` in one chain does not skip later chains), the two layers
have to agree on what is reachable.

## Default-drop policy (phase 1)

The `skale` chain policy is **drop**. Everything not explicitly accepted is
dropped:

- conntrack `established/related` and loopback traffic
- ssh (detected via `getservbyname`), DNS (53), HTTP (80), HTTPS (443),
  watchdog (3009, 311), and monitoring ports (8080, 9100) when monitoring is
  enabled
- ICMP `destination-unreachable`, `source-quench`, `time-exceeded`
  (no `echo-request` - the node does not answer ping)
- ICMPv6 neighbor discovery and error types (required for IPv6 to function
  under a drop policy on an `inet` chain)
- the **sChain ports envelope**: `tcp dport <base_port>..<base_port + 8191>`
  (128 sChain slots x 64 ports). Fine-grained filtering inside the envelope
  is enforced by the skale-admin chains, which run earlier (priority 0) and
  end with a terminal drop for each active sChain range.

The envelope base port is resolved in this order:

1. `SCHAIN_BASE_PORT` environment variable
2. `node_base_port` from `node_data/node_config.json` - the node's
   registration port, saved by skale-admin at registration and backfilled
   from the contracts on every admin restart for existing nodes
3. `schain_base_port` from `node_data/node_config.json` - fallback for
   passive and fair nodes, where it holds the single hosted chain's base
   port (a valid anchor); on active nodes this field keeps its passive-mode
   meaning and is never written by registration
4. `10000` (the default registration port)

Before flipping the policy to drop, `setup_firewall`:

1. ensures every accept rule above exists (the flip is the last step, so a
   failure mid-way leaves the node reachable - it fails open);
2. validates that the port range of every live `skale-*` chain fits into the
   envelope, and aborts with an actionable error otherwise;
3. verifies the ssh and conntrack accept rules are actually present in the
   live chain.

The saved config (`/etc/nft.conf.d/skale/base.conf`) snapshots the chain with
its policy and includes the skale-admin chain configs, so a reboot applies
everything atomically.

### Operator notes

- Existing nodes get the new policy on the next `skale node update` (or
  `skale node configure-firewall`). The setup is idempotent.
- Ship the skale-admin release (which backfills `node_base_port` on admin
  restart) before the node-cli release that flips the policy - existing
  custom-port nodes then anchor correctly with no manual step.
- If the node was registered with a non-default base port and
  `node_config.json` does not contain `node_base_port` yet (admin has not
  restarted on the new version), set `SCHAIN_BASE_PORT` to the registration
  port. The validation step catches the mismatch and refuses to flip the
  policy until it is fixed.
- Custom services listening on other ports must be allowed in
  `/etc/nft.conf.d/skale/user.conf` (included at the top of the `skale`
  chain) - plain nftables rule lines, e.g. `tcp dport 5000 counter accept`.
- Rollback: set `FIREWALL_DEFAULT_DROP=False` in the environment and rerun
  `skale node configure-firewall`. Emergency manual rollback:
  `nft add chain inet firewall skale '{ policy accept ; }'`.
- Ports published by Docker containers over bridge networking bypass the
  input hook entirely (they are governed by Docker's forward chains); this
  firewall governs host-network services, which includes skaled.

### Known trade-off of the envelope

Envelope ports with no active sChain are accepted by the firewall and answer
as *closed* (kernel RST) instead of *filtered*, and a stray listener bound
inside the envelope would be reachable. Ports of active sChains are protected
exactly as before by the skale-admin chains. Removing this trade-off is the
goal of phase 2.

## Planned: sChain ports set (phase 2)

Goal: unused sChain ports show as *filtered* - the envelope accept is
replaced by an accept driven by an interval set that skale-admin maintains
in lock-step with its chains. Validated end-to-end by a container prototype
(traffic + reboot persistence) on 2026-09-01.

Design:

- node-cli declares an interval set in `base.conf` and swaps the envelope
  accept for a set-driven accept in the `skale` chain:

  ```
  set schain_ports {
      type inet_service
      flags interval
  }
  ...
  tcp dport @schain_ports counter accept
  ```

- skale-admin keeps its per-sChain priority-0 base chains **exactly as they
  are** (per-peer accepts + terminal range drop). The only addition: one set
  element added/removed together with the chain lifecycle:

  ```
  add element inet firewall schain_ports { 10064-10127 }
  ```

  Traversal: peer/public traffic accepted at priority 0 continues into
  `skale`, matches the set, accepted. Strangers on consensus ports die on
  the priority-0 terminal drop. Ports with no element fall to policy drop -
  filtered, even if something listens there.

- persistence: each saved chain config in `/etc/nft.conf.d/skale/chains/`
  stays self-contained by re-declaring the set with just its element - nft
  merges elements across declarations of the same set, so a reboot restores
  chains and elements atomically with no re-sync:

  ```
  chain skale-x { ... }
  set schain_ports { type inet_service ; flags interval ; elements = { 10064-10127 } }
  ```

- rollout, each step safe under version skew:
  1. node-cli release: declare the set, add the `@schain_ports` accept,
     seed elements from the live `skale-*` chain ranges at configure time
     (`get_dynamic_chain_port_ranges`), **keep the envelope**.
  2. skale-admin release: manage elements on chain create/cleanup, include
     the element re-declaration in saved chain configs, extend the firewall
     health check to verify the element.
  3. node-cli: remove the envelope accept once every live chain range has a
     matching set element (checked at configure time; abort otherwise).

Alternative considered: a verdict map (`type inet_service : verdict`,
elements `{ range : jump skale-x }`) with per-sChain **regular** chains.
Same filtering result, plus per-chain rules only evaluated for their own
ports - but it requires migrating every existing base chain and changing
skale-admin's chain creation, so the set variant is preferred.
