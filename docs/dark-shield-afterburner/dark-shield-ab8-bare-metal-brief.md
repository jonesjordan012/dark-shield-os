# AB-8 Bare Metal, Translated
**Draft v0.1 — engineering grounding for the First Citizen's bare-metal access**
Date: 2026-10-12

Your AB-8 ruling says the First Citizen gets **bare metal access** to the interplanetary UI and paradigm system, while the NPU governs the prostheses. "Bare metal governs the machine." This note translates that into what is actually true on your Linux Mint laptop — what bare metal can mean, what is reachable, and what the honest limits are. Plain language, no assumed knowledge.

## The two rooms

Every Linux machine has two rooms:

- **The kernel's room.** The kernel lives here. It talks to hardware directly and can see all of memory. Engineers call this *ring 0*.
- **Everyone else's room.** Every program you run — Chrome, Python, starscape.py — lives here (*ring 3*). These programs cannot touch hardware or each other's memory. When they need something from the machine, they knock on the kernel's door with a **system call**: "please read this file," "please draw this."

**"Bare metal access" = getting keys to the kernel's room.** On Linux there are real keys for this. They are not metaphors:

- **root** — the master key. Opens every door, including ones you shouldn't open.
- **Capabilities** — the master key broken into individual teeth. `CAP_SYS_RAWIO` (capability number 17) is the single tooth that grants direct hardware access without granting everything else. This is the one that matters for AB-8.
- **Kernel modules** — code that moves *into* the kernel's room and lives there. Maximum power, maximum danger: a bug crashes the whole machine.
- **eBPF** — the modern answer: small programs the kernel lets you run inside its room, but *verified safe first*. Observation and governance without the crash risk.

## What is actually reachable on your Dell Latitude (Mint)

1. **Direct memory (`/dev/mem`) is locked by default.** The kernel's build option `CONFIG_STRICT_DEVMEM` restricts it — on x86, plain RAM access through `/dev/mem` is *not* allowed; only PCI hardware regions and BIOS areas are reachable. (Source: `mem(4)` Linux man page, kernel.org.) So "the Citizen reads any byte of RAM directly" is off the table on a stock Mint install. This is a deliberate lock, and Dark Shield would have to decide whether to pick it — see the honest limit below.

2. **Direct hardware I/O exists but is guarded.** The old x86 doorways `iopl()` / `ioperm()` (talking to hardware ports directly) still exist, but the kernel only grants them to processes holding `CAP_SYS_RAWIO`. (Source: Linux `capability.h`, capability 17; iopl documentation.) Real, usable — and genuinely dangerous: touching the wrong port can freeze the machine. This is exactly the "deep access, lit room" territory.

3. **The screen: DRM/KMS is the honest "bare metal" for the UI.** Your interplanetary UI does not need to bypass the kernel to own the display. Linux's display system (DRM/KMS — Direct Rendering Manager / Kernel Mode Setting) lets a program become the *master* of the screen: no X server, no window manager, no desktop between your code and the pixels. This is how Wayland compositors and game consoles draw. For AB-8, "bare metal access to the interplanetary UI" most honestly means: **a dedicated, privileged session that is DRM master of the display.**

4. **The keyboard and mouse: evdev.** Raw input events straight from the devices, no desktop in between. Same session, same privilege set.

5. **The pragmatic 95%.** You do not need a custom kernel or a kernel module for All Systems Go. A minimal session — one virtual console (TTY), running as a dedicated identity, granted exactly the capabilities it needs (DRM master for the screen, evdev for input, read access to hardware state) and nothing else — *is* bare metal in every sense that matters for your design. The last 5% (true ring-0 code) is kernel modules or eBPF, and eBPF is where a future Dark Shield would put kernel-level governance — including, one day, enforcement of the Echo itself.

## What this means for your design

- **All Systems Go is implementable, not mythical.** It is a privileged session shape: one TTY, minimal trusted code, exact capabilities, the interplanetary UI drawn directly through DRM. Your laptop can do this today.

- **Your "no god-mode" ruling has an engineering twin.** You ruled that AB-8 avoids god-mode through NPU governance of perception. Linux agrees with the *shape* of your ruling: capabilities are finer-grained than root for a reason. AB-8 should never run as the master key. It should hold a hand-picked set of teeth — display, input, hardware state — while the NPU holds the prostheses and the Echo holds the memory. *Bare metal governs the machine; the NPU governs perception* translates to: **the Citizen's session holds hardware capabilities; the kernel (and one day the NPU) holds the audit.**

- **"The deeper the access, the more lit the room" is already Linux's direction.** The whole history of Linux security is moving from one master key (root) toward many small keys (capabilities) plus verifiable observation (eBPF, audit). Your principle is the design philosophy the kernel has been converging on for thirty years. AB-8 is philosophically native to Linux.

- **The honest limit: Secure Boot and kernel lockdown.** On machines with Secure Boot enabled, even root cannot load unsigned kernel modules or poke at `/dev/mem` — the kernel enforces a lockdown on itself. Think of it as the anchors' veto having a real-world twin: there are doors the Citizen cannot open even in All Systems Go, because the machine's own constitution forbids it. When Dark Shield one day defines its boot chain, this is where the Reality Anchors would live — below the Citizen, in the part of the system that even sovereignty cannot override without breaking the seal.

## Status

Draft for your review. Nothing here changes existing canon; it grounds AB-8's "bare metal" in implementable Linux mechanics. When you want it, the natural next hands-on step is a tiny experiment on your Mint laptop: a program that claims a TTY and queries the DRM display — the first true All Systems Go spark. Say the word and we'll build it in one of your short windows.

## Sources

- `mem(4)` man page (kernel.org, mirrored via mywebuniversity.com): `CONFIG_STRICT_DEVMEM` limits `/dev/mem` on x86 — RAM access not allowed, PCI/BIOS regions only. (checked 2026-10-12)
- Linux `capability.h`: `CAP_SYS_RAWIO` (17) — "Allow ioperm/iopl access." (checked 2026-10-12)
- iopl/ioperm documentation (github.com/eantcal/ioperm README): root + `CAP_SYS_RAWIO` required to raise the I/O privilege level. (checked 2026-10-12)
