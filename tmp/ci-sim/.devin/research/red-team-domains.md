# Red Team domain coverage: tool matrix + primary sources

Date: 2026-10-09. Spec: `.devin/scratch/optimized_ready.md`. Sibling doc:
`.devin/research/rea-analysis.md` (REA port decisions).

## Method & verification levels

- Every source below was surfaced and its content sampled via `web_search`
  result payloads (title/URL/extracted body text) on 2026-10-09; no URL was
  written from memory. Level tags: **[doc]** official tool docs/repo,
  **[paper]** peer-reviewed (IEEE S&P / USENIX / NDSS / CCS / PLDI / OSDI /
  DIMVA / ACSAC / WOOT), **[std]** standard/framework/methodology
  (OWASP / NIST / MITRE / ETSI / PTES / OSSTMM), **[forum]** primary community
  disclosure (e.g., original PMKID write-up).
- Critical tool claims cross-validated by >=2 sources; flagged `xv` in the
  matrix (e.g., sqlmap technique count: sqlmap.org vs wiki; PMKID: hashcat
  forum + hcxdumptool README + hashcat wiki + wifite2).
- Integration status: `via-rea` = covered by `rea-agents` CLI wrapper
  (`extensions/rea-ops`); `wrap` = new `extensions/offsec-tools` subcommand;
  `engine` = heavyweight service invoked via own runner (daemon/docker);
  `reference` = methodology cited inside skill docs, not wrapped; `out` =
  deferred with reason.

## 1. Domain x Tool x Status matrix

| Domain | Tool | Role | Status | xv |
|---|---|---|---|---|
| RE/native | `rea-agents` CLI (Hopper/Ghidra/IDA/artifacts/.NET/APK/firmware/browser providers) | analysis engine orchestration | wrap (`rea-ops`) | xv |
| RE/native | Ghidra (headless) | disasm/decompile, SLEIGH | via-rea (engine behind CLI) | xv |
| RE/native | angr | symbolic exec / CFG / decompile library | wrap candidate (Py lib) | xv |
| RE/native | radare2 / rizin | disasm, diff (radiff2), patch | wrap candidate | xv |
| RE/native | capa + capa-rules | capability detection (PE/ELF/.NET/shellcode), ATT&CK/MBC pivots | wrap candidate | xv |
| RE/native | FLOSS | deobfuscated-string extraction | wrap candidate | xv |
| RE/native | YARA | pattern rules, classification | wrap candidate | xv |
| RE/native | x64dbg / pwndbg / GEF | Windows/Linux debug | reference (interactive GUI/TTY) | |
| RE/native | ILSpy / dnSpy(Ex) | .NET decompile/debug | via-rea (dotnet provider) / wrap candidate | xv |
| RE/native | Qiling | cross-plat binary emulation (PE/ELF/Mach-O/UEFI) | wrap candidate | xv |
| RE/native | SoK S&P'16 (angr authors) | technique taxonomy ground truth | reference | |
| Web/injection | OWASP WSTG + Top10 + ASVS + MASVS checks | methodology + coverage checklist | reference (drives skill playbooks) | xv |
| Web/injection | ZAP (daemon mode, `ascan`) | passive+active DAST | engine (Docker/daemon) | xv |
| Web/injection | sqlmap | SQLi detect+exploit, DB fingerprint | wrap | xv |
| Web/injection | nuclei + nuclei-templates | template YAML vuln scan (HTTP/DNS/TCP/file) | wrap | xv |
| Web/injection | ffuf | content/vhost/param fuzzing | wrap | xv |
| Web/injection | Juice Shop | local benchmark target | reference (held-out tests) | xv |
| Web/injection | Doupé/Cova/Vigna DIMVA'10 | scanner-limitation evidence (crawling bottleneck) | reference | |
| Net/infra | nmap (+NSE) | discovery, version/OS detect, vuln scripts | wrap | xv |
| Net/infra | masscan | Internet-scale port scan (async) | wrap | xv |
| Net/infra | ZMap | single-port Internet survey | reference (Linux, niche) | xv |
| Net/infra | NetExec (nxc) | network service/AD enumeration+exec checks | wrap (Linux/WSL) | xv |
| Net/infra | impacket | protocol toolkit (SMB/MSRPC/Kerberos/LDAP) | wrap (enum tools only; no credential-harvest commands) | xv |
| Net/infra | enum4linux-ng | SMB/RPC/LDAP enum, JSON/YAML out | wrap | xv |
| Net/infra | testssl.sh | TLS/SSL cipher/protocol/vuln audit | wrap | xv |
| Net/infra | OpenVAS/GVM | full vuln scanner w/ VT feed | engine (Docker) | xv |
| Net/infra | Metasploit Framework | verify-only auxiliary/scanner modules; exploit modules out-of-scope by default | engine (msfconsole RPC) | xv |
| Net/infra | NIST SP 800-115 / PTES / OSSTMM 3 | engagement methodology + reporting discipline | reference | xv |
| Net/infra | CISA KEV / NVD / MITRE ATT&CK (+mitreattack-python) | prioritization + technique mapping | reference (data feeds) | xv |
| Wireless/RF | aircrack-ng suite (airmon/airodump/aircrack) | capture, WEP PTW/FMS, WPA dict crack | wrap (Linux) | xv |
| Wireless/RF | Kismet | passive Wi-Fi/BT/SDR discovery | wrap | xv |
| Wireless/RF | bettercap `wifi.*` | recon, deauth, PMKID, rogue AP beacons | wrap (Linux) | xv |
| Wireless/RF | hcxdumptool + hcxtools (hcxpcapngtool) | PMKID/EAPOL capture → hashcat 22000 | wrap (Linux) | xv |
| Wireless/RF | hashcat (-m 22000/16800) | WPA handshake/PMKID cracking | wrap | xv |
| Wireless/RF | wifite2 | orchestrated audit (handshake/PMKID/WPS) | wrap candidate | xv |
| Wireless/RF | wifipumpkin3 + hostapd | rogue AP / captive portal (module-gated) | engine (opt-in module) | xv |
| Wireless/RF | FragAttacks tool (vanhoefm) | frag/agg vuln tester | wrap candidate | xv |
| Wireless/RF | URH | SDR protocol reverse/fuzz/simulate | wrap candidate | xv |
| Wireless/RF | GNU Radio / HackRF One / rtl_433 | RF capture + ISM decode | wrap candidate (hw-gated) | xv |
| Wireless/RF | Proxmark3 (RRG/Iceman) | RFID/NFC analysis (LF/HF) | wrap candidate (hw-gated) | |
| Wireless/RF | KRACK CCS'17 / Dragonblood / FragAttacks papers | protocol-flaw ground truth | reference | xv |
| Firmware | binwalk v3 (Rust rewrite) | signature scan, extract, entropy | wrap (via rea fw provider OR offsec-tools) | xv |
| Firmware | unblob | 78+ format recursive extraction | wrap (Linux; via rea fw provider) | xv |
| Firmware | EMBA | full pipeline: extract→static→dynamic→SBOM→CVE report | engine (Linux, installer -d) | xv |
| Firmware | FACT_core / firmwalker | FS-content analysis / config+keyword scan | wrap candidates | |
| Firmware | Firmadyne/FirmAE (papers) | full-system emulation lineage; EMBA embeds FirmAE kernels | via EMBA | xv |
| Firmware | Firmalice / Avatar / P2IM / HALucinator / Fuzzware / IoTFuzzer | research grounding for emulation+auth-bypass+fuzzing design | reference | xv |
| Firmware | OWASP FSTM (9 stages) | assessment methodology | reference (skill playbook) | xv |
| Firmware | MITRE EMB3D / ETSI EN 303 645 | embedded threat model + IoT baseline requirements | reference | xv |
| Mobile | OWASP MASVS / MASTG (+MASWE, atomic tests) | standard + test catalog | reference (skill playbook) | xv |
| Mobile | MobSF | static+dynamic, API, frida orchestration | engine (Docker) | xv |
| Mobile | jadx / apktool | dex→Java decompile, resource decode | via-rea (jadx provider) + wrap | xv |
| Mobile | frida / objection | runtime instrumentation, pinning bypass | wrap (dynamic; needs rooted emu/device) | xv |
| Mobile | APKLab (VS Code) | integrated RE bench (quark/apktool/jadx/apk-mitm) | reference | |
| Mobile | TaintDroid OSDI'10 / FlowDroid PLDI'14 | taint-analysis ground truth (dynamic vs static) | reference | xv |
| Cross | MITRE ATT&CK STIX (cti repo, mitreattack-python) | technique tagging for findings | reference | xv |
| Cross | CWE/NVD/KEV | vuln identity + exploit-priority feeds | reference | xv |

## 2. Sources: RE / binary analysis (22)

| # | Source | URL | Type | Validates |
|---:|---|---|---|---|
| 1 | Ghidra docs portal | http://ghidradocs.com/ | doc | headless analyzer, PyGhidra, SLEIGH, decompiler internals |
| 2 | NSA Ghidra repo | https://github.com/NationalSecurityAgency/ghidra | doc | scope: disasm/decompile/graph/script, multi-arch, interactive+automated |
| 3 | angr site | https://angr.io/ | doc | static+dynamic, concolic, CFG, AIL decompile, BSD, Py3.12+ |
| 4 | angr docs | https://docs.angr.io/en/latest/ | doc | API surface (SimState, analyses, SimProcedure); also exposes `angr.mcp` |
| 5 | capa site | https://mandiant.github.io/capa/ | doc | PE/ELF/.NET/shellcode capability detection, ATT&CK+MBC pivots, 890+ rules |
| 6 | capa repo | https://github.com/mandiant/capa/ | doc | CLI standalone + Py lib (flare-capa), backends IDA/Ghidra/BN/CAPE/DRAKVUF |
| 7 | capa-rules | https://github.com/mandiant/capa-rules | doc | rule namespaces (anti-analysis, collection, c2, persistence, impact) |
| 8 | Rizin Handbook | https://book.rizin.re/ | doc | rizin CLI tools, disasm/debug/patch/scripting |
| 9 | Radare2 book | https://book.rada.re/ | doc | r2 suite: radiff2 diffing, rafind2 pattern search |
| 10 | ILSpy repo | https://github.com/icsharpcode/ilspy | doc | .NET decompiler, cross-plat Avalonia, ILSpyCmd dotnet tool, ReadyToRun |
| 11 | dnSpyEx repo | https://github.com/dnSpyEx/dnSpy | doc | maintained fork: .NET debug+edit, no-source debugging, .NET 8/4.8 |
| 12 | dnSpy (orig) | https://github.com/dnSpy/dnSpy/blob/master/README.md | doc | original feature set (IL edit, metadata tables, dnlib) |
| 13 | x64dbg docs | http://x64dbg.readthedocs.io/ | doc | command/plugin/trace-file spec surface |
| 14 | x64dbg help | https://help.x64dbg.com/en/latest/commands/ | doc | command categories (breakpoints, tracing, memory ops) |
| 15 | pwndbg repo | https://github.com/pwndbg/pwndbg | doc | GDB/LLDB plugin, RE/exploit-dev focus, embedded/kernel support table |
| 16 | YARA docs | https://yara.readthedocs.io/en/latest/ | doc | rule model: strings+condition, hex/text/regex, modules (PE, Cuckoo) |
| 17 | YARA repo docs | https://github.com/VirusTotal/yara/blob/master/docs/commandline.rst | doc | `yara RULES TARGET` CLI contract, yarac compile, -s print-strings |
| 18 | FLOSS usage | https://github.com/mandiant/flare-floss/blob/master/doc/usage.md | doc | static/stack/tight/decoded string classes, `--no-string-type`, renderers |
| 19 | SoK S&P'16 (PDF) | https://oaklandsok.github.io/papers/shoshitaishvili2016.pdf | paper | systematized offensive binary-analysis techniques (angr framework) |
| 20 | SoK DOI record | https://asu.elsevierpure.com/en/publications/sok-state-of-the-art-of-war-offensive-techniques-in-binary-analys/ | paper | IEEE SP 2016 pp.138-157, DOI 10.1109/SP.2016.17, DARPA CGC dataset eval |
| 21 | Qiling docs | https://docs.qiling.io/en/latest/howto/ | doc | `Qiling(argv, rootfs)` API, rootfs/fs-mapper, AFL++ unicorn-mode fuzzing |
| 22 | Qiling repo | https://www.github.com/qilingframework/qiling | doc | multi-OS/multi-arch emulation, instrumentation, hot-patch, IDA plugin |

## 3. Sources: Web application / injection (22)

| # | Source | URL | Type | Validates |
|---:|---|---|---|---|
| 1 | WSTG portal | https://wstg.owasp.org/ | std | flagship testing methodology for web apps/services |
| 2 | WSTG project page | https://owasp.org/www-project-web-security-testing-guide/ | std | versioned-link convention (`v42/...`) for citations |
| 3 | sqlmap site | https://sqlmap.org/ | doc | 5 injection techniques (site) vs 6 incl. inline (wiki); discrepancy noted |
| 4 | sqlmap Features | https://github.com/sqlmapproject/sqlmap/wiki/Features | doc | 6 SQLi + 7 non-SQL (NoSQL, GraphQL, LDAP, XPath, SSTI, XXE, HQL) |
| 5 | sqlmap Techniques | https://github.com/sqlmapproject/sqlmap/wiki/Techniques | doc | boolean/time/error/UNION/stacked/inline mechanics, `--timeless` HTTP/2 |
| 6 | sqlmap Introduction | https://github.com/sqlmapproject/sqlmap/wiki/Introduction | doc | detect→fingerprint→enumerate→takeover workflow; `-d` direct connect |
| 7 | ZAP active scan | https://www.zaproxy.org/docs/desktop/start/features/ascan/ | doc | ascan = attack; X-ZAP-Initiator header; logic vulns out of scanner scope |
| 8 | ZAP API | https://www.zaproxy.org/docs/api/ | doc | `ascan.scan(target,...)`, poll status, xmlreport; the daemon automation contract |
| 9 | ZAP scan policy | https://www.zaproxy.org/docs/desktop/start/features/scanpolicy/ | doc | per-scan rule selection = controllable blast radius |
| 10 | nuclei overview | https://docs.projectdiscovery.io/opensource/nuclei/overview | doc | YAML-template vuln scanner for apps/infra/cloud/networks |
| 11 | nuclei template structure | https://docs.projectdiscovery.io/templates/structure | doc | id+info+protocol+matchers+extractors DSL |
| 12 | nuclei-templates repo | https://github.com/Projectdiscovery/Nuclei-Templates/ | doc | community corpus; KEV coverage stats (CISA 454 / VulnCheck 1449) |
| 13 | Template creation guide | https://github.com/projectdiscovery/nuclei-templates/blob/main/TEMPLATE-CREATION-GUIDE.md | doc | classification cve-id/cwe-id/cvss; severity enum; verified metadata |
| 14 | ffuf repo | https://github.com/ffuf/ffuf | doc | Go web fuzzer; `FUZZ` keyword in URL/header/POST; matchers/filters |
| 15 | ffuf wiki | https://github.com/ffuf/ffuf/wiki | doc | full flag reference (CLI flags page) |
| 16 | ffuf workshop | https://github.com/joohoi/ffuf-workshop/ | doc | author-maintained usage deck, multi-wordlist autocalibration patterns |
| 17 | OWASP Top 10:2021 | https://owasp.org/Top10/2021/index.html | std | A01-A10 risk taxonomy (BAC, crypto, injection, misconfig, SSRF...) |
| 18 | Juice Shop project | https://owasp.org/projects/juice-shop | std | deliberately-vulnerable flagship app; tool guinea-pig for JS-heavy SPAs |
| 19 | Juice Shop site | https://juice-shop.github.io/juice-shop/ | doc | challenge coverage: Top10 + ASVS + Automated Threat Handbook + API Top10 + CWE |
| 20 | DevGuide vuln-apps | https://github.com/OWASP/DevGuide/blob/main/docs/en/07-training-education/01-vulnerable-apps/01-juice-shop.md | doc | JS as safe practice target rationale |
| 21 | Johnny Can't Pentest (PDF) | https://adamdoupe.com/publications/black-box-scanners-dimva2010.pdf | paper | DIMVA'10 eval of 11 scanners: crawling is the bottleneck; classes of vulns wholly missed → scanners ≠ pentest |
| 22 | Johnny Can't Pentest record | https://eldorado.tu-dortmund.de/items/6ad2a528-b284-45f0-9275-625eb06951e4 | paper | venue record (TU Dortmund Eldorado) |

## 4. Sources: Network / infrastructure (26)

| # | Source | URL | Type | Validates |
|---:|---|---|---|---|
| 1 | NIST SP 800-115 | https://csrc.nist.gov/pubs/sp/800/115/final | std | technical guide for security testing/assessment; supersedes SP 800-42 |
| 2 | NIST pub page | https://www.nist.gov/publications/technical-guide-information-security-testing-and-assessment | std | citation record (Scarfone et al., Sep 2008) |
| 3 | PTES About | http://www.pentest-standard.org/index.php/The_Penetration_Testing_Execution_Standard:About | std | engagement phases standard |
| 4 | PTES Tech Guidelines | http://www.pentest-standard.org/index.php/PTES%5FTechnical%5FGuidelines | std | baseline tool/procedure catalog per phase |
| 5 | PTES Reporting | http://www.pentest-standard.org/index.php/Reporting | std | report = scope+attack-path+impact+remediation (drives finding format) |
| 6 | PTES FAQ/tree | https://pentest-standard.readthedocs.io/en/master/faq.html | std | standard's scope/levels definition |
| 7 | Nmap book | https://nmap.org/book/ | doc | official guide; NSE, evasion, performance chapters |
| 8 | Nmap reference | https://nmap.org/book/man.html | doc | full CLI contract (18 sections); defines the wrapper arg surface |
| 9 | Nmap docs hub | https://nmap.org/docs.html | doc | doc index |
| 10 | ZMap paper page | https://www.usenix.org/conference/usenixsecurity13/technical-sessions/paper/durumeric | paper | USENIX Sec'13: IPv4 survey <45min single host; ethics/"good citizenship" section |
| 11 | ZMap PDF | https://zmap.io/paper.pdf | paper | architecture + measurement evidence |
| 12 | ZMap ACM | https://dl.acm.org/doi/10.5555/2534766.2534818 | paper | proceedings record |
| 13 | masscan man | https://github.com/robertdavidgraham/masscan/blob/master/doc/masscan.8.markdown | doc | async scanner, up to 25M pps, nmap-compatible output |
| 14 | masscan repo | https://raw.githubusercontent.com/robertdavidgraham/masscan/master/README.md | doc | build (gcc/make), nmap comparison |
| 15 | impacket README | https://github.com/fortra/impacket/blob/master/README.md | doc | SMB1-3/MSRPC/Kerberos/LDAP/TDS Python classes; Fortra-maintained |
| 16 | impacket PyPI | https://pypi.org/project/impacket/0.13.0/ | doc | packaging/install vector |
| 17 | NetExec wiki | https://www.netexec.wiki/ | doc | network service exploitation/enum automation, open-source |
| 18 | NetExec repo | https://github.com/pennyw0rth/netexec | doc | BSD-2, `nxc`, AD-focused protocol ops |
| 19 | NetExec-Wiki repo | https://github.com/Pennyw0rth/NetExec-Wiki | doc | doc source for wiki |
| 20 | OSSTMM 3 PDF | https://mirror.math.princeton.edu/pub/parrot/misc/openbooks/security/OSSTMM.3.pdf | std | channel-agnostic testing methodology, rav attack-surface metric |
| 21 | OpenVAS repo | https://github.com/greenbone/openvas | doc | Greenbone CE scanner, VT feed, docker `ghcr.io/greenbone/openvas-scanner` |
| 22 | Metasploit docs tree | https://github.com/rapid7/metasploit-framework/tree/master/docs | doc | docs.metasploit.com source; module option contract (`run <proto>://`) |
| 23 | MSF ssl_version module | https://github.com/rapid7/metasploit-framework/blob/master/modules/auxiliary/scanner/ssl/ssl_version.rb | doc | auxiliary/scanner verify pattern; CVE/CWE/RFC references in-module |
| 24 | CISA KEV | https://www.cisa.gov/known-exploited-vulnerabilities-catalog | std | authoritative exploited-in-wild catalog (CSV/JSON feeds) |
| 25 | KEV↔ATT&CK mappings | https://ctid.mitre.org/mappings/external/kev/all-data.html | std | capability-group mapping of exploited CVEs |
| 26 | testssl.sh repo | https://github.com/testssl/testssl.sh | doc | TLS ciphers/protocols/flaws CLI, zero-install bash, docker image |

## 5. Sources: Wireless / RF (25)

| # | Source | URL | Type | Validates |
|---:|---|---|---|---|
| 1 | aircrack-ng doc | https://www.aircrack-ng.org/doku.php?id=aircrack-ng | doc | WEP PTW/FMS + WPA dict; SIMD cracking |
| 2 | airodump-ng doc | https://www.aircrack-ng.org/doku.php?id=airodump-ng | doc | raw 802.11 capture, GPS logging, output formats |
| 3 | aircrack getting_started | https://www.aircrack-ng.org/doku.php?id=getting_started | doc | chipset/monitor-mode prerequisites; "don't use suite under Windows" |
| 4 | Kismet docs | https://www.kismetwireless.net/docs/ | doc | Wi-Fi/BT/SDR capture sources, per-phy config |
| 5 | bettercap wifi | https://www.bettercap.org/modules/wifi/ | doc | recon/deauth/PMKID/rogue-beacon/bruteforce module contract |
| 6 | KRACK paper | https://papers.mathyvanhoef.com/ccs2017.pdf | paper | key-reinstallation vs 4-way/PeerKey/FT; all-zero key on Android 6 |
| 7 | KRACK ACM | https://dl.acm.org/doi/10.1145/3133956.3134027 | paper | CCS'17 record (Vanhoef & Piessens) |
| 8 | Dragonblood paper | https://papers.mathyvanhoef.com/dragonblood.pdf | paper | WPA3/SAE side-channel + downgrade analysis; released tooling |
| 9 | Dragonblood ePrint | https://eprint.iacr.org/2019/383.pdf | paper | IACR record |
| 10 | FragAttacks paper | https://www.usenix.org/system/files/sec21-vanhoef.pdf | paper | USENIX Sec'21: 3 design flaws in aggregation/fragmentation, WEP→WPA3 |
| 11 | fragattacks.com | https://www.fragattacks.com/ | doc | vulnerability catalog + test tool pointer |
| 12 | fragattacks repo | https://github.com/vanhoefm/fragattacks/ | doc | released client/AP tester, CVE list, live USB |
| 13 | wifite2 PMKID notes | https://github.com/derv82/wifite2/blob/master/PMKID.md | doc | hcxdumptool→hcxpcapngtool→hashcat -m16800 pipeline contract |
| 14 | PMKID original write-up | https://hashcat.net/forum/thread-7717.html | forum | atom's discovery thread (clientless PMKID); the primary disclosure |
| 15 | hcxdumptool README | https://github.com/ZerBea/hcxdumptool/blob/master/README.md | doc | capture daemon scope, companion hcxtools, caution section (own-network scope) |
| 16 | hashcat WPA wiki | https://hashcat.net/wiki/doku.php?id=cracking_wpawpa2 | doc | mode 22000 pipeline; no-cleaning rule for pcapng; cap2hashcat |
| 17 | hcxpcapngtool man | https://manpages.debian.org/bookworm/hcxtools/hcxpcapngtool.1.en.html | doc | pcapng→hash formats, message-pair field semantics, nonce-error-corrections |
| 18 | URH paper | https://www.usenix.org/system/files/conference/woot18/woot18-paper-pohl.pdf | paper | WOOT'18: Interpretation→Analysis→Generation→Simulation workflow; SDR-agnostic |
| 19 | URH repo | https://github.com/jopohl/urh | doc | demod/decoding/fuzzing/stateful simulation; PyPI install |
| 20 | Proxmark3 repo | https://github.com/RfidResearchGroup/proxmark3 | doc | Iceman fork: LF/HF RFID, simulate/sniff, Lua scripting, cross-plat builds |
| 21 | Proxmark3 README | https://github.com/RfidResearchGroup/proxmark3/blob/master/README.md | doc | install/verify matrix incl. Windows/Termux, supported hardware |
| 22 | HackRF One docs | https://hackrf.readthedocs.io/en/stable/hackrf_one.html | doc | 1MHz-6GHz half-duplex SDR spec |
| 23 | HackRF product page | https://greatscottgadgets.com/hackrf/one/ | doc | open-hardware, GNU Radio/SDR# compat |
| 24 | rtl_433 repo | https://github.com/merbanan/rtl_433/ | doc | ISM-band (433/868/315/345/915MHz) receiver, RTL-SDR/SoapySDR |
| 25 | wifipumpkin3 | https://github.com/P0cL4bs/wifipumpkin3 + https://docs.wifipumpkin3.com/ | doc | rogue-AP/MITM framework, hostapd backend, module system |

## 6. Sources: Firmware / embedded (27)

| # | Source | URL | Type | Validates |
|---:|---|---|---|---|
| 1 | unblob repo | https://github.com/onekey-sec/unblob | doc | 78+ formats, recursive carving, unknown-chunk carving, plugin API |
| 2 | ONEKEY extraction docs | https://docs.onekey.com/platform-guide/how-analyze/firmware-extraction/ | doc | extraction pipeline stages (signature→carve→decompress→recurse) |
| 3 | unblob guide | https://github.com/onekey-sec/unblob/blob/bcdc89e4/docs/guide.md | doc | CLI contract (`unblob FILE`, depth, extractors list) |
| 4 | binwalk repo | https://github.com/ReFirmLabs/binwalk | doc | v3 Rust rewrite; signature ID, extract, entropy |
| 5 | binwalk releases | https://github.com/ReFirmLabs/binwalk/releases | doc | feature deltas (sasquatch/jefferson integration, capstone disasm scan, native Windows) |
| 6 | EMBA repo | https://github.com/e-m-b-a/emba | doc | extract→static→emulation→SBOM→web report pipeline; `installer.sh -d` |
| 7 | EMBA feature overview | https://github.com/e-m-b-a/emba/wiki/Feature-overview | doc | module map (P55 unblob, S09 version-detect, S12 checksec...) |
| 8 | EMBA wiki home | https://github.com/e-m-b-a/emba/wiki | doc | run contract: `./emba -f fw.bin -l logdir -p profile` → html_report |
| 9 | EMBA installation | https://github.com/e-m-b-a/emba/wiki/Installation | doc | dependency list incl. binwalk/unblob/qemu/FirmAE kernels/testssl/nikto/msf |
| 10 | EMBA releases | https://github.com/e-m-b-a/emba/releases | doc | emulation success-rate evolution (6%→79% lineage), SBOM pivot |
| 11 | Firmadyne paper | https://www.ndss-symposium.org/wp-content/uploads/2017/09/towards-automated-dynamic-analysis-linux-based-embedded-firmware.pdf | paper | NDSS'16: full-system emulation at scale; 23,035 images, 887 vulnerable |
| 12 | Firmadyne repo paper | https://raw.githubusercontent.com/firmadyne/firmadyne/master/paper/paper.pdf | paper | primary artifact + code repo |
| 13 | Firmadyne BU mirror | https://seclab.bu.edu/papers/firmadyne-ndss2016.pdf | paper | cross-copy (Egele/BU) |
| 14 | FirmAE paper | https://dl.acm.org/doi/fullHtml/10.1145/3427228.3427294 | paper | ACSAC'20: arbitrated emulation heuristics |
| 15 | FirmAE PDF | https://syssec.kaist.ac.kr/pub/2020/kim_acsac2020.pdf | paper | Firmadyne 16.28% → FirmAE 79.36% emulation rate; 12 0-days |
| 16 | Firmalice page | https://www.ndss-symposium.org/ndss2015/ndss-2015-programme/firmalice-automatic-detection-authentication-bypass-vulnerabilities-binary-firmware/ | paper | NDSS'15 record |
| 17 | Firmalice PDF | https://sefcom.asu.edu/publications/firmalice-automatic-detection-of-authentication-bypass-vulnerabilities-ndss15.pdf | paper | symbolic-exec auth-bypass model; 2/3 devices had detectable backdoors |
| 18 | Avatar page | https://www.ndss-symposium.org/ndss2014/ndss-2014-programme/avatar-framework-support-dynamic-security-analysis-embedded-systems-firmwares/ | paper | NDSS'14 record |
| 19 | Avatar PDF | https://www.s3.eurecom.fr/docs/ndss14_zaddach.pdf | paper | emulator↔hardware I/O forwarding (Avatar2 arbitration) |
| 20 | P2IM paper | https://www.usenix.org/system/files/sec20-feng.pdf | paper | USENIX'20: automatic peripheral modeling, 79% firmware execution, 7 bugs |
| 21 | HALucinator paper | https://www.usenix.org/system/files/sec20-clements.pdf | paper | USENIX'20: HAL-based re-hosting + AFL vuln discovery |
| 22 | IoTFuzzer paper | https://bruceqczhao.github.io/assets/ndss18/NDSS18.pdf | paper | NDSS'18: fuzz via official-app protocol logic, no firmware needed; 15 vulns |
| 23 | Fuzzware paper | https://www.usenix.org/system/files/sec22-scharnowski.pdf | paper | USENIX'22: MMIO modeling, 3.25× coverage, 95.5% input-space reduction |
| 24 | EMB3D site | https://emb3d.mitre.org/ | std | embedded threat model: properties→threats→mitigations |
| 25 | EMB3D paper | https://emb3d.mitre.org/assets/EMB3D_Paper_09-23-24.pdf | std | threat-maturity model + ATT&CK/CWE alignment |
| 26 | OWASP FSTM | https://github.com/scriptingxss/owasp-fstm | std | 9-stage firmware assessment methodology (recon→exploitation) |
| 27 | ETSI EN 303 645 | https://www.etsi.org/deliver/etsi_en/303600_303699/303645/03.01.02_20/en_303645v030102a.pdf | std | consumer-IoT baseline requirements (v3.1.2) |

## 7. Sources: Mobile (21)

| # | Source | URL | Type | Validates |
|---:|---|---|---|---|
| 1 | MASVS | https://mas.owasp.org/MASVS/ | std | industry standard for mobile app security verification |
| 2 | MASTG | https://mas.owasp.org/MASTG/ | std | testing+RE manual mapping MASVS controls via MASWE |
| 3 | MASTG atomic tests | https://mas.owasp.org/MASTG/tests/ | std | per-weakness test structure: overview/steps/observation/evaluation |
| 4 | MASTG techniques | https://mas.owasp.org/MASTG/techniques/ | std | technique catalog (instrumentation, network, RE) |
| 5 | OWASP MAS project | https://owasp.org/www-project-mobile-app-security/ | std | flagship status; MASVS+MASWE+MASTG trio |
| 6 | MobSF dynamic-analyzer | https://github.com/MobSF/docs/blob/master/dynamic_analyzer_docker.md | doc | Frida for Android 5-11, Xposed 4.1-4.4, Corellium iOS ≥17 |
| 7 | MobSF docker run | https://github.com/MobSF/docs/blob/master/running_mobsf_docker.md | doc | rooted-device constraint (API≤30), host-gateway flag |
| 8 | MobSF frida integration | https://deepwiki.com/MobSF/Mobile-Security-Framework-MobSF/3.1.2-frida-instrumentation-(android) | doc | script dirs default/dump/rpc/aux; spawn vs session modes |
| 9 | MobSF env.py | https://github.com/MobSF/Mobile-Security-Framework-MobSF/blob/master/mobsf/DynamicAnalyzer/views/android/environment.py | doc | MobSFy setup: CA install + frida/xposed agent push |
| 10 | MobSF frida_core.py | https://github.com/MobSF/Mobile-Security-Framework-MobSF/blob/2b08dd05/mobsf/DynamicAnalyzer/views/android/frida_core.py | doc | script assembly (enum_class, string_catch, trace_class...) |
| 11 | Frida docs home | https://frida.re/docs/home/ | doc | JS-injected QuickJS instrumentation, multi-OS incl. iOS/Android/QNX |
| 12 | Frida site | https://frida.re/ | doc | bindings npm/PyPI/Swift/.NET/Qml/Go/C |
| 13 | Frida Android docs | https://frida.re/docs/android/ | doc | usb-device attach pattern for tool building |
| 14 | Frida JS API | https://frida.re/docs/javascript-api/ | doc | ApiResolver etc., the scripting surface for wrappers |
| 15 | objection repo | https://github.com/sensepost/objection | doc | runtime mobile exploration on Frida; pinning bypass, keychain dump, pip install |
| 16 | jadx repo | https://github.com/skylot/jadx | doc | dex/aar/aab→Java, manifest decode, deobfuscator, `output-format json` |
| 17 | Apktool repo | https://github.com/iBotPeaches/Apktool/ | doc | decode→rebuild cycle, smali debugging, project structure |
| 18 | APKLab | https://github.com/ariakis/APKLab | doc | VS Code bench composing quark/apktool/jadx/apk-mitm/uber-apk-signer |
| 19 | TaintDroid paper | https://static.usenix.org/event/osdi10/tech/full_papers/Enck.pdf | paper | OSDI'10 dynamic taint tracking, 14% overhead; found 68 misuses/30 apps |
| 20 | TaintDroid ACM | https://dl.acm.org/doi/10.5555/1924943.1924971 | paper | proceedings + TOCS extension (10.1145/2619091) |
| 21 | FlowDroid paper | https://dl.acm.org/doi/10.1145/2594291.2594299 | paper | PLDI'14 static taint analysis; DroidBench: 93% recall / 86% precision |

## 8. Cross-validated critical claims (sample)

| Claim | Sources ≥2 |
|---|---|
| sqlmap detects+exploits multiple SQLi techniques incl. blind/error/UNION/stacked (+non-SQLi families) | sqlmap.org (§3.3) + wiki Features/Techniques (§3.4-3.5) |
| ZAP active scan is an attack on target; needs owned/authorized scope | ZAP ascan doc (§3.7) + API doc (§3.8) |
| Automated scanners miss logic vulns / crawling is the bottleneck | ZAP ascan (§3.7) + DIMVA'10 (§3.21) |
| PMKID enables clientless WPA attack; hash mode 22000/16800 pipeline | hashcat forum t-7717 (§5.14) + hcxdumptool README (§5.15) + hashcat wiki (§5.16) + wifite2 (§5.13) |
| Every Wi-Fi device class vulnerable to KRACK/FragAttacks (protocol-level) | KRACK CCS'17 (§5.6-5.7) + FragAttacks USENIX'21 (§5.10-5.12) |
| Full-system emulation coverage: Firmadyne 16% → FirmAE ~79% | Firmadyne NDSS'16 (§6.11) + FirmAE ACSAC'20 (§6.14-15) + EMBA releases (§6.10) |
| MobSF dynamic analysis requires rooted Android ≤11/API≤30 or Corellium | MobSF docs (§7.6-7.7) |
| capa covers PE/ELF/.NET/shellcode w/ ATT&CK+MBC mapping | capa site (§2.5) + repo (§2.6) + rules repo (§2.7) |
| REA supplies jadx/binwalk/unblob providers (caller-supplied binaries) | rea-analysis.md §3 + unblob/binwalk/jadx docs |

## 9. Honest limits

- Windows host: wireless suite, hcxdumptool, unblob, EMBA, Kismet are
  Linux-dependent; `doctor` in wrappers must report `unsupported_platform`
  rather than fail silently (REA convention: "missing evidence is unknown").
- Firmware emulation (FirmAE-class) and MobSF dynamic need nested virt /
  rooted emulator; capability flag `requires_vm: true`.
- No tool is executed during this task; wrappers ship `doctor`/`capabilities`
  only until ROE fields are wired (Fase 2).

### 9.1 WSL execution tiers (Windows host strategy)

`offsec-tools` wrapper gains a `backend: native|wsl|docker` resolver:
`doctor` probes `wsl.exe --status` / `wsl -l -v` and Docker; dispatch runs
`wsl -d <distro> -- <tool>` or the matching container. Tiers per tool:

| Tier | Tools | Notes |
|---|---|---|
| wsl2-ready | unblob (docker), EMBA (docker, `installer.sh -d`), NetExec, enum4linux-ng, testssl.sh, masscan, nmap, nuclei, ffuf, sqlmap, jadx, apktool, binwalk v3, radare2/rizin, capa, FLOSS, YARA, angr, Qiling | CLI/Docker workloads; no special device access |
| wsl2-gated | hashcat (GPU needs vendor driver WSL support; CPU fallback ok), MobSF (docker + emulator on host via `host.docker.internal`), ZAP daemon (docker) | works with caveats; `doctor` checks each prerequisite |
| wsl2-fragile | hcxdumptool/hcxtools capture, aircrack-ng suite, Kismet, bettercap wifi | monitor mode + injection need usbipd-win USB-adapter passthrough; offline pcap analysis works without hardware |
| native-linux-only | wifipumpkin3 rogue AP, Firmadyne/FirmAE-style system emulation, UEFI low-level | report `unsupported_platform` unless a real Linux host/remote agent exists |

RF/SDR (HackRF, rtl_433, Proxmark3): same gate; USB passthrough via
usbipd-win is required and per-device verified by `doctor`.
