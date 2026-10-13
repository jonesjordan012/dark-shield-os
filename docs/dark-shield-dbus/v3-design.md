# Dark Shield D-Bus API — v3 Design (ObjectManager + Versioning)

*Design note, October 9, 2026. Status: designed, parked pending prototype.*

For Dark Shield D-Bus API v3, add both API version contracts and ObjectManager support as first-class platform features. This strengthens the Moonlight ecosystem while remaining aligned with the universe, galaxy, and Moon Universe model described in Dark Shield OS Vision Summary.

## Versioning Contract

### Bus Names

Freeze major versions at the bus level.

```
org.darkshield.v1.Universe
org.darkshield.v1.Gravity
...
org.darkshield.v2.Universe
org.darkshield.v2.Gravity
...
org.darkshield.v3.Universe
org.darkshield.v3.Gravity
...
```

Rule: major version change = new bus namespace. Minor version change = same namespace.

### Object Paths

Version root namespace: `/org/darkshield/v3`

Example:

```
/org/darkshield/v3/universe
/org/darkshield/v3/gravity
/org/darkshield/v3/...
```

This allows v2 clients and v3 clients to coexist.

### Version Interface

Every object implements:

```xml
<interface name="org.darkshield.Versioned">

  <property name="ApiVersion" type="u" access="read"/>
  <property name="MajorVersion" type="u" access="read"/>
  <property name="MinorVersion" type="u" access="read"/>
  <property name="CompatibilityLevel" type="s" access="read"/>

  <method name="GetCapabilities">
    <arg name="capabilities" type="as" direction="out"/>
  </method>

</interface>
```

Example:

```
ApiVersion: 3, MajorVersion: 3, MinorVersion: 1, CompatibilityLevel: "v3"
```

### Capability Negotiation

Rather than assuming features exist, `GetCapabilities` returns:

```
moonlight
afterburner
antigravity
gravity-v2
...
```

This future-proofs clients.

## Root ObjectManager

At `/org/darkshield/v3`, implement:

```xml
<interface name="org.freedesktop.DBus.ObjectManager">

  <method name="GetManagedObjects">
    <arg type="a{oa{sa{sv}}}" direction="out"/>
  </method>

  <signal name="InterfacesAdded">
    <arg type="o"/>
    <arg type="a{sa{sv}}"/>
  </signal>

  <signal name="InterfacesRemoved">
    <arg type="o"/>
    <arg type="as"/>
  </signal>

</interface>
```

This is the standard mechanism used by NetworkManager, BlueZ, and ModemManager.

### Managed Object Tree

```
/org/darkshield/v3
├── universe
├── gravity
├── darkmatter
├── eclipse
├── antigravity
├── afterburner
├── consensus
├── observatory
├── anchor
├── galaxies
└── moons
```

All discovery comes from `GetManagedObjects()`.

## Moon Universe Objects

Dynamic path: `/org/darkshield/v3/moons/moon0091`

```xml
<interface name="org.darkshield.MoonUniverse">
```

Properties:

```xml
<property name="MoonId" type="s" access="read"/>
<property name="State" type="u" access="read"/>
<property name="Strategy" type="s" access="read"/>
<property name="RiskScore" type="d" access="read"/>
<property name="EvolutionScore" type="d" access="read"/>
<property name="Trusted" type="b" access="read"/>
```

### Enumerated Universe States

Replace string states with uint32 enums:

```
0  CREATED
1  SYNCING
2  READY
3  RUNNING
4  PAUSED
5  FAILED
6  PROMOTION_PENDING
7  PROMOTED
8  DESTROYED
```

## Galaxy Objects

Dynamic path: `/org/darkshield/v3/galaxies/development`

```xml
<interface name="org.darkshield.Galaxy">
```

Properties:

```xml
<property name="GalaxyId" type="s" access="read"/>
<property name="Intent" type="s" access="read"/>
<property name="GravityScore" type="d" access="read"/>
<property name="EvolutionPotential" type="d" access="read"/>
```

Galaxies represent evolving human intentions such as Development, Research, Communication, Learning, and Creativity.

## Promotion Request Objects

Instead of passing raw IDs (`PR-552`), create objects:

`/org/darkshield/v3/promotions/PR552`

Interface: `org.darkshield.Promotion`

Properties: `RequestId`, `UniverseId`, `Confidence`, `AnchorApproved`, `Status`

Lifecycle:

```
REQUESTED
EVALUATING
APPROVED
REJECTED
APPLIED
```

## Anchor Security Levels

Reality Anchors protect system integrity. Define:

```
0  USER
1  GALAXY
2  SYSTEM
3  CORE
```

```xml
<property name="SecurityLevel" type="u" access="read"/>
```

## Feature Flags Interface

Optional experimental interface:

```xml
<interface name="org.darkshield.Features">

  <method name="ListFeatures">
    <arg name="features" type="a{sb}" direction="out"/>
  </method>

</interface>
```

Example:

```
moonlight: true
afterburner: true
antigravity: true
selfmodifying: false
```

## Recommended v3 Root Introspection

```
/org/darkshield/v3
│
├── ObjectManager
├── Versioned
│
├── universe
├── gravity
├── darkmatter
├── eclipse
├── antigravity
├── afterburner
├── consensus
├── observatory
├── anchor
│
├── galaxies/*
├── moons/*
├── promotions/*
└── futures/*
```

## Assessment

The addition of `org.freedesktop.DBus.ObjectManager`, `org.darkshield.Versioned`, capability negotiation, dynamic Moon/Galaxy objects, enum-based lifecycle states, and promotion objects would make Dark Shield D-Bus API v3 resemble a mature Linux subsystem architecture comparable to the organizational patterns used by NetworkManager and systemd, while preserving the Moonlight, Antigravity, Data Gravity, and Reality Anchor concepts defined in Dark Shield OS Vision Summary.

## Parked v3 remainder

Still open from the v3 scope: SELinux/AppArmor D-Bus busconfig policy per service, tied to the Reality Anchor trust story (TPM, Secure Boot, dm-verity).
