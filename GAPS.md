# Known spec gaps

Calculation-input fields (see `CONTRIBUTING.md`) that a part's core parameter
set calls for, but are not published anywhere in that part's **primary**
manufacturer datasheet. These are not reachability failures or oversights:
the sheet was read, it just doesn't quote the value. Often this happens on
abbreviated small-signal datasheets that skip gate-charge or thermal tables
entirely.

Closing one of these honestly requires either a newer/fuller datasheet
revision from the same manufacturer, or a real bench measurement. See
`CONTRIBUTING.md` -> "Measuring a gap yourself" if you have the equipment
and want to contribute a measured value.

Do not fill these from a different manufacturer's datasheet for the same
generic part number unless you also update `datasheet_url`/`manufacturers`
to match and confirm the part is truly the same die (see the `variants` rule
in CONTRIBUTING.md); mixing an unrelated vendor's numbers into an existing
citation is worse than leaving the gap.

## mosfet

| part | missing | why |
|------|---------|-----|
| `2n7000` | Qg, Qgs, Qgd, Vsd, trr, Rth(JC) | onsemi 2N7000TA/D (current rev, July 2023) omits gate-charge and body-diode-dynamics tables entirely. TO-92 also has no case tab, so Rth(JC) isn't meaningful/published; only Rth(JA). |
| `bss138` | trr | onsemi datasheet's body-diode table stops at VSD/IS; no reverse-recovery time is quoted. |
| `bss138` | Rth(JC) | SOT-23 has no separate junction-to-case path; only Rth(JA) is published. |
| `bs170` | Qg, Qgs, Qgd, Coss, Crss, Rth(JC), Rth(JA), Vsd, trr | onsemi BS170/D is a minimal 2-page sheet: only Ciss (max) and a combined ton/toff (not broken into td(on)/tr/td(off)/tf) are given. No thermal-resistance table at all, no gate-charge section, no body-diode section. |

## power (regulator)

| part | missing | why |
|------|---------|-----|
| `mt3608` | Rth(JC), Rth(JA) | Aerosemi's datasheet gives max junction temp (160C) and thermal-shutdown threshold (155C) but no thermal-resistance table at all. |
| `tp4056` | dropout (numeric) | NanJing Top Power's datasheet discusses "dropout mode" narratively (charge current folds back when VCC-VBAT headroom is insufficient) but never quotes a numeric dropout voltage in the electrical characteristics table. |

## Needs datasheet (reachability, not a data gap)

Unlike the tables above, these aren't cases where the primary sheet was read
and came up short: the primary sheet itself couldn't be reached. Tracked
separately per the fill-spec workflow; hand these to a human to download and
drop in `parts-db/datasheets/<class>/`, or revisit once reachability
changes.

Resolved: `l7905`/`lm7912`/`lm7915` (ST's `l79.pdf`, DS0428 Rev 24) was
hand-delivered and all three are now filled (Iq, Rth(JC), Rth(JA), dropout,
Vin abs max). No longer blocked, nothing left in this table right now.

Note: the related **100mA TO-92** negative family (79L05/79L12/79L15) is
*not* in this bucket: TI publishes `lm79l.pdf` directly and it fetches fine;
`79l05.json`'s `datasheet_url` was switched to that TI sheet since ST's
`l79l.pdf` is equally blocked and TI is already a listed manufacturer for
that part.

## transistor_bjt

Rth(JC)/Rth(JA) is only part of the required bar for power BJTs (see
CONTRIBUTING.md); the many small-signal parts in this category (BC547-class,
2N3904-class, S9012-9018, etc.) correctly have no Rth entry at all, that is
not a gap, it is expected for that class.

| part | missing | why |
|------|---------|-----|
| `tip31c` | f_T, Rth(JC), Rth(JA) | ST's TIP31C sheet (Rev 1, April 2006) has no thermal-resistance table and no transition-frequency spec at all; only Ptot at two case/ambient points is given. |
| `tip32c` | f_T, Rth(JC), Rth(JA) | Same ST-family sheet gap as tip31c (its PNP complement). |
| `tip122` | f_T | Diotec's TIP120...TIP122 sheet gives a small-signal current gain (hfe) at 1MHz but never a transition-frequency (f_T) spec. |
| `tip127` | f_T | Same Diotec TIP125...TIP127 sheet gap as tip122 (its PNP complement). |
| `bc517` | f_T | onsemi's BC517 sheet has an f_T characterization graph but no numeric table value; noted inline in the part's own `extra.ft`. |
| `b772` | Rth(JA) | ST's 2SB772 sheet gives only Rth(JC) (10 C/W); no junction-to-ambient figure is published. |
| `2sd882` | Rth(JC), Rth(JA) | NEC's 2SD882 sheet has no thermal-resistance table at all, despite being a TO-126 medium-power part. |

## transistor_germanium

Rth is only expected for power-oriented germanium parts (ac128); small-signal
switching parts (2n404) not quoting it is expected, same pattern as small-signal
BJTs above, not a gap.

| part | missing | why |
|------|---------|-----|
| `nkt275` | Vce(sat)/Vbe(sat), Rth, confirmed pinout | Newmarket Transistors is defunct with no surviving primary datasheet found. Electrical data comes from a period catalog scan reached only via an aggregator mirror, cross-checked against one independent secondary lookup; neither includes a saturation voltage or a package pin diagram. Marked `verified: false`; see the part's own gotchas before using the pinout for anything physical. |

## opamp

| part | missing | why |
|------|---------|-----|
| `tl072` | Iout | TI's TL07x family sheet only publishes a short-circuit current spec (+-26mA typ) for the newer TL07xH grade; the standard TL072C table (the one that matches this generic part) has no output-current row at all. |
| `tl074` | Iout | Same TI TL07x sheet gap as tl072 (shares the identical document and C-grade table, quad version). |
| `tl082` | Iout | Same gap in TI's TL08x sheet (the TL081/082/084 family document follows the identical C-grade-vs-H-grade split). |

## transistor_jfet

Newly audited (scripts/find_gaps.py gained a transistor_jfet check as part of
adding mpf102). Rth is expected to be absent on small-signal JFETs, not a gap.

| part | missing | why |
|------|---------|-----|
| `2n5457` | gfs (forward transconductance) | onsemi's sheet does not publish this entry's data under a gfs field; not found in the currently-cited datasheet extract. |
| `j201` | gfs (forward transconductance) | same gap as 2n5457, pre-dates this audit category existing. |

## comparator

Newly audited (scripts/find_gaps.py gained a comparator check as part of
adding lmv331).

| part | missing | why |
|------|---------|-----|
| `lm311`, `lm339`, `lm393` | Ibias | genuinely not stored in any of these three pre-existing entries; not a naming mismatch. |

Not a gap, just a note for anyone reading the audit script's raw output:
`lm311`/`lm339`/`lm393` show up under "output type" but don't need it; they
already store this under the key `output` (e.g. "open-collector..."), the
substring check just doesn't match that key name.

## diode

| part | missing | why |
|------|---------|-----|
| `1n34a` | Ir, Rth, and effectively everything beyond what's already stored | manufacturers field is "various (NOS and current production)" with no single primary datasheet to cite; this is a generically-sourced germanium part with real part-to-part spread (the existing entry's own gotchas say as much and it's marked `verified: false`). There is no primary sheet to read further values from without fabricating a source. |

Not a gap, just a note for anyone reading the audit script's raw output:
`bat54` shows up under "Rth (power)" but doesn't need it; it's a small-signal
SOT-23 part with no separate junction-to-case path, and its required
rectifier/signal group (VRRM, IF(av), IFSM, VF, IR, trr) is already complete.
