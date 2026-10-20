"""Presets: Vollständigkeit, gültige Werte, Standard-Preset = Standardeinstellungen, Permalink-Grenzen."""

import pytest

import bkr_constants as C
import bkr_evaluation as ev
import bkr_presets as P


def test_every_preset_has_help_and_all_keys():
    assert set(C.PRESETS) == set(C.PRESET_HELP)
    for name, preset in C.PRESETS.items():
        assert set(preset) == set(P.PRESET_KEYS), name
        assert C.PRESET_HELP[name]


def test_preset_values_are_inside_the_regler_bounds():
    for name, preset in C.PRESETS.items():
        assert preset["net"] in C.NET_TYPES and preset["root"] in C.ROOTS, name
        assert C.N_MIN <= preset["n"] <= C.N_MAX and C.K_MIN <= preset["k"] <= C.K_MAX and 0 <= preset["seed"] <= C.SEED_MAX, name


def test_default_preset_equals_the_default_settings_and_is_first():
    first = next(iter(C.PRESETS))
    assert ev.Settings(**C.PRESETS[first]) == ev.Settings()


def test_presets_differ_from_each_other():
    values = [tuple(sorted(p.items())) for p in C.PRESETS.values()]
    assert len(set(values)) == len(values)


def test_setting_specs_cover_every_preset_key():
    assert set(P.PRESET_KEYS.values()) == set(P.SETTING_SPECS)


def test_setting_defaults_equal_the_constants():
    assert {k: s.default for k, s in P.SETTING_SPECS.items()} == {
        "net_select": C.DEFAULT_NET, "n_slider": C.DEFAULT_N, "k_slider": C.DEFAULT_K, "root_select": C.DEFAULT_ROOT, "seed_input": C.DEFAULT_SEED}


@pytest.mark.parametrize("key,raw,expected", [
    ("n_slider", "100", 100), ("n_slider", "3", C.N_MIN), ("n_slider", "99999", C.N_MAX), ("n_slider", "abc", None), ("n_slider", ["200"], 200),
    ("k_slider", "0", C.K_MIN), ("k_slider", "50", C.K_MAX), ("k_slider", "4", 4), ("seed_input", "-4", 0), ("seed_input", "9999999", C.SEED_MAX),
    ("net_select", "grid", "grid"), ("net_select", "ring", None), ("root_select", "edge", "edge"), ("root_select", "x", None),
])
def test_permalink_values_are_clamped_or_rejected(key, raw, expected):
    assert P._coerce(P.SETTING_SPECS[key], raw) == expected


def test_url_parameters_are_distinct():
    params = [s.url_param for s in P.SETTING_SPECS.values()]
    assert len(set(params)) == len(params)


def test_bounds_of_choice_settings_are_first_and_last_option():
    assert P.bounds("net_select") == ("delaunay", "grid") and P.bounds("root_select") == ("center", "edge")
    assert P.bounds("n_slider") == (C.N_MIN, C.N_MAX) and P.bounds("k_slider") == (C.K_MIN, C.K_MAX)
