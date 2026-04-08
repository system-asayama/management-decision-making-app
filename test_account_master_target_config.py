#!/usr/bin/env python3
"""勘定科目マスタの組換え先設定テスト"""

import os

os.environ.setdefault('DATABASE_URL', 'sqlite:///:memory:')

from app.blueprints.decision import (
    _PL_FIELDS,
    _PL_FIELD_GROUPS,
    _BS_FIELDS,
    _BS_FIELD_GROUPS,
    _get_target_field_config,
    _normalize_target_field,
)


def test_legacy_mcr_target_keys_are_migrated_to_pl_keys():
    """旧MCRキーはPLキーへ正規化される"""
    assert _normalize_target_field('mcr', 'labor_cost_manufacturing') == 'labor_cost'
    assert _normalize_target_field('mcr', 'beginning_raw_material') == 'beginning_inventory'
    assert _normalize_target_field('mcr', 'depreciation_manufacturing') == 'capital_regeneration_cost'



def test_mcr_uses_pl_target_fields():
    """製造原価報告書の組換え先はPLと同じ定義を使う"""
    config = _get_target_field_config('mcr')

    assert config['default_statement'] == 'PL'
    assert config['allowed_fields'] is _PL_FIELDS
    assert config['field_groups'] is _PL_FIELD_GROUPS


def test_pl_and_bs_configs_remain_unchanged():
    """既存のPL/BS設定はそのまま維持する"""
    pl_config = _get_target_field_config('pl')
    bs_config = _get_target_field_config('bs')

    assert pl_config['default_statement'] == 'PL'
    assert pl_config['allowed_fields'] is _PL_FIELDS
    assert pl_config['field_groups'] is _PL_FIELD_GROUPS

    assert bs_config['default_statement'] == 'BS'
    assert bs_config['allowed_fields'] is _BS_FIELDS
    assert bs_config['field_groups'] is _BS_FIELD_GROUPS
