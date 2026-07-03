"""
partinfo schema -- canonical data model for electronic component entries.
all parts stored as JSON files under parts/; this module validates them.
"""

from __future__ import annotations
from typing import Literal, Optional
from pydantic import BaseModel, Field


PinType = Literal[
    "power", "ground", "input", "output", "bidirectional",
    "passive", "analog", "clock", "reset", "nc"
]

PackageTemplate = Literal[
    "dip", "sip", "sot23", "sot23-5", "sot23-6",
    "to92", "to220", "to247",
    "qfp", "qfn", "lqfp", "tqfp",
    "soic", "tssop", "ssop",
    "module",   # breakout boards, ESP32 modules, Arduino, etc.
    "custom",
]

Category = Literal[
    "audio",
    "opamp",
    "transistor_bjt",
    "transistor_jfet",
    "transistor_mosfet",
    "transistor_germanium",
    "diode",
    "timer",
    "comparator",
    "thyristor",
    "logic",
    "power",
    "mcu",
    "module",
    "interface",
    "sensor",
    "driver",
    "memory",
    "display",
    "rf",
    "other",
]


class Pin(BaseModel):
    pin: int | str          # int for DIP/SIP, str for named pins (ESP32 GPIO4)
    name: str               # house/functional label, normalized across the family
    type: PinType
    description: str
    # verbatim label from the cited datasheet, set only when it differs from name.
    # the same silicon carries different vendor labels (TI QA = Nexperia Q0), so
    # this is per-datasheet, tied to the part's datasheet_url. not a lookup key --
    # name + pin + type stay the source of truth; this is a documented alias.
    datasheet_name: Optional[str] = None
    alternate: list[str] = Field(default_factory=list)  # alternate functions (same vendor)


class Package(BaseModel):
    template: PackageTemplate
    pin_count: int
    pins: list[Pin]
    ascii: Optional[str] = None     # pre-rendered ascii diagram
    notes: Optional[str] = None


class Specs(BaseModel):
    """
    all fields optional -- include what's relevant for the part type.
    voltage in V, current in mA, frequency in Hz, power in mW/W as noted.
    """
    vs_min_v:       Optional[float] = None
    vs_max_v:       Optional[float] = None
    vs_typ_v:       Optional[float] = None
    iq_ma:          Optional[float] = None      # quiescent current
    iout_max_ma:    Optional[float] = None
    pout_mw:        Optional[float] = None
    pd_max_mw:      Optional[float] = None      # max power dissipation
    gain_db_min:    Optional[float] = None
    gain_db_max:    Optional[float] = None
    bw_hz:          Optional[float] = None
    freq_max_hz:    Optional[float] = None
    vf_v:           Optional[float] = None      # diode forward voltage
    vce_sat_v:      Optional[float] = None
    hfe_min:        Optional[int]   = None
    hfe_max:        Optional[int]   = None
    idss_ma:        Optional[float] = None      # JFET drain current
    vgs_off_v:      Optional[float] = None      # JFET pinch-off
    rds_on_ohm:     Optional[float] = None      # MOSFET on-resistance
    vgs_th_v:       Optional[float] = None      # MOSFET gate threshold
    flash_kb:       Optional[int]   = None
    ram_kb:         Optional[int]   = None
    eeprom_b:       Optional[int]   = None
    cpu_mhz:        Optional[int]   = None
    gpio_count:     Optional[int]   = None
    # thermal resistance, degC/W. the one pair of values universal enough across
    # every device class, and simple enough (always a bare number for a given
    # mount/package), to warrant a typed field rather than living only in extra.
    # when a datasheet gives typ+max or multiple mounting conditions, this holds
    # the single conservative figure (max, or worst-case/no-heatsink); the full
    # detail with conditions still belongs in extra alongside it.
    rth_jc_cw:      Optional[float] = None
    rth_ja_cw:      Optional[float] = None
    extra: dict[str, str | float | int] = Field(default_factory=dict)  # anything else


class Variant(BaseModel):
    """a specific manufacturer part whose pinout differs from the generic entry's
    common pinout. the same generic number (2N2222) ships from different vendors
    with genuinely different physical pin assignments; a variant records one such
    divergence, tied to its own datasheet. the parent Part's `packages` pinout is
    the common/typical case; variants are the exceptions."""
    mpn: str                        # specific part number: "P2N2222A"
    manufacturer: str               # "onsemi"
    package: str                    # package this pinout applies to: "TO-92"
    pins: list[Pin]                 # this variant's pinout for that package
    datasheet_url: Optional[str] = None
    verified: bool = False          # pins checked against this variant's datasheet
    note: Optional[str] = None      # what differs and why it matters


class Part(BaseModel):
    id: str                         # lowercase, hyphenated slug: "lm386", "esp32-s3"
    name: str                       # canonical name: "LM386"
    aliases: list[str] = Field(default_factory=list)
    full_name: str
    manufacturers: list[str] = Field(default_factory=list)
    category: Category
    subcategory: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    description: str
    packages: dict[str, Package]    # key = package name: "DIP-8", "QFN-48"
    specs: Optional[Specs] = None
    typical_application: Optional[str] = None
    gotchas: list[str] = Field(default_factory=list)
    related: list[str] = Field(default_factory=list)   # ids of related parts
    datasheet_url: Optional[str] = None     # canonical manufacturer datasheet
    # verified = pin data checked against the primary datasheet. false means the
    # entry is hand-entered but unaudited; datasheet_url may still be populated.
    verified: bool = False
    # specific manufacturer parts whose pinout differs from the common one above.
    # empty for the vast majority; populated only where vendors genuinely diverge.
    variants: list[Variant] = Field(default_factory=list)
    source: Literal["human", "ollama", "claude"] = "human"
    # a human confirmed a non-human-sourced entry is correct, without rewriting
    # source (which stays an honest, permanent record of who actually wrote it).
    # the "verify before trusting" warning is suppressed once this is true.
    human_reviewed: bool = False
    notes: Optional[str] = None


# -- reference entries -------------------------------------------------------
# fundamentals (ohm's law, color codes, RF math). a separate content type from
# parts: own schema, own renderer, own CLI namespace. stored under references/.

RefTopic = Literal[
    "dc",           # ohm's law, dividers, power
    "passive",      # RC/LR, reactance, resonance, color codes, E-series
    "digital",      # logic thresholds, number bases, timing
    "power",        # regulator/converter math, battery
    "rf",           # transmission lines, VSWR, dB, antennas
    "thermal",      # dissipation, theta-ja
    "tables",       # AWG, standard values, ASCII, prefixes
    "math",         # general EE math
    "other",
]


class Variable(BaseModel):
    symbol: str
    meaning: str
    unit: Optional[str] = None


class Formula(BaseModel):
    expr: str                       # "V = I * R"
    description: Optional[str] = None
    vars: list[Variable] = Field(default_factory=list)


class RefTable(BaseModel):
    title: Optional[str] = None
    headers: list[str]
    rows: list[list[str]]


class RefEntry(BaseModel):
    id: str                         # slug: "ohms-law", "resistor-color-code"
    title: str                      # "Ohm's Law"
    topic: RefTopic
    tags: list[str] = Field(default_factory=list)
    summary: str                    # one-line
    body: Optional[str] = None      # markdown prose explanation
    formulas: list[Formula] = Field(default_factory=list)
    tables: list[RefTable] = Field(default_factory=list)
    examples: list[str] = Field(default_factory=list)
    gotchas: list[str] = Field(default_factory=list)
    related: list[str] = Field(default_factory=list)   # ids of refs or parts
    see_also_url: Optional[str] = None
    source: Literal["human", "ollama", "claude"] = "human"
    human_reviewed: bool = False
