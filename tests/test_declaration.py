"""The declaration: the catalogue declared from code, as registration and
`meridian plugin upload` read it."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from meridian.v1 import sidecar_pb2

from kalshi.declaration import DECLARATION
from kalshi.declared import BARS, CATALOGUE, SAMPLE_DATA


def test_one_live_dataset_of_prices_and_quotes_served_not_kept() -> None:
    [live, _, _] = CATALOGUE
    assert (live.key, live.vendor, live.day_time_zone, live.day_end_minute) == (
        "live",
        "Kalshi",
        "Etc/UTC",
        0,
    )
    assert list(live.data_types) == ["meridian.v1.Price", "meridian.v1.Quote"]
    assert live.venue_id == "", "the venue's ID is resolved at run time, never invented"
    licence = live.licence_default
    assert licence is not None and not licence.kept, "served, not kept"
    assert not (licence.display or licence.derived_use or licence.personal_use), (
        "a default claiming nothing: the deployment's licence replaces it"
    )


def test_its_outcomes_pushed_and_kept() -> None:
    # Contract v23: each contract's outcome, recorded unasked, kept so that
    # its versions are read back.
    [_, outcomes, _] = CATALOGUE
    assert (outcomes.key, outcomes.vendor, outcomes.venue_id) == ("outcomes", "Kalshi", "")
    assert list(outcomes.data_types) == ["meridian.v1.Outcome"]
    assert list(outcomes.modes) == [sidecar_pb2.OBSERVATION_MODE_PUSH]
    licence = outcomes.licence_default
    assert licence is not None and licence.kept
    assert not (licence.display or licence.derived_use or licence.personal_use)


def test_no_key_needed_and_sample_data_a_developers_setting() -> None:
    # The data role's settings (spec/plugin-pages-follow-their-role): one
    # environment and no credential, so sample data alone, labelled as the
    # SDK's helper labels it.
    assert isinstance(DECLARATION.settings, tuple)
    [setting] = DECLARATION.settings
    assert (setting.name, setting.developer, setting.secret) == (SAMPLE_DATA, True, False)
    assert (setting.label, setting.default) == ("Sample data", False)
    assert DECLARATION.storage is not None


def test_upload_reads_the_same_declaration() -> None:
    printed = subprocess.run(
        [str(Path(sys.executable).parent / "meridian-declaration"),
         "kalshi.declaration:DECLARATION"],
        capture_output=True, text=True, check=True,
    )  # fmt: skip
    datasets = json.loads(printed.stdout)["catalogue"]["datasets"]
    assert [d["key"] for d in datasets] == ["live", "outcomes", "bars"]
    assert [d["modes"] for d in datasets] == [["pull", "stream"], ["push"], ["pull", "push"]]


def test_its_bars_pushed_and_pulled_kept_on_new_yorks_day() -> None:
    # 0.11.0 (rulings 624, 625 and 629): the bars dataset, of the lake's bar
    # kind, on Kalshi's day, New York's: its daily candles end at midnight
    # there.
    [_, _, bars] = CATALOGUE
    assert bars is BARS
    assert (bars.key, bars.vendor, bars.venue_id) == ("bars", "Kalshi", "")
    assert list(bars.data_types) == ["meridian.v1.Bar"]
    assert list(bars.modes) == [
        sidecar_pb2.OBSERVATION_MODE_PULL,
        sidecar_pb2.OBSERVATION_MODE_PUSH,
    ]
    assert (bars.day_time_zone, bars.day_end_minute, bars.history) == ("America/New_York", 0, 30)
    licence = bars.licence_default
    assert licence is not None and licence.kept
    assert not (licence.display or licence.derived_use or licence.personal_use)
