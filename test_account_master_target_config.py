#!/usr/bin/env python3
"""勘定科目マスタの組換え先設定テスト"""

import os
from pathlib import Path

os.environ.setdefault('DATABASE_URL', 'sqlite:///:memory:')

from app.blueprints.decision import (
    _PL_FIELDS,
    _PL_FIELD_GROUPS,
    _BS_FIELDS,
    _BS_FIELD_GROUPS,
    _get_target_field_config,
    _normalize_target_field,
)
from app.models_decision import RestructuredPL


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


def test_inventory_breakdown_fields_are_available_in_cost_of_sales_group():
    """売上原価グループに棚卸高の内訳項目が追加されている"""
    assert _PL_FIELDS['beginning_inventory'] == '（1）期首棚卸高（合計）'
    assert _PL_FIELDS['beginning_inventory_material'] == '　　①期首材料棚卸高'
    assert _PL_FIELDS['beginning_inventory_wip'] == '　　②期首仕掛品棚卸高'
    assert _PL_FIELDS['beginning_inventory_goods'] == '　　③期首商品棚卸高'
    assert _PL_FIELDS['ending_inventory'] == '（3）期末棚卸高（合計）'
    assert _PL_FIELDS['ending_inventory_material'] == '　　①期末材料棚卸高'
    assert _PL_FIELDS['ending_inventory_wip'] == '　　②期末仕掛品棚卸高'
    assert _PL_FIELDS['ending_inventory_goods'] == '　　③期末商品棚卸高'

    cost_group = next(group for group in _PL_FIELD_GROUPS if group['label'] == '2. 売上原価')
    assert cost_group['options'] == [
        'beginning_inventory',
        'beginning_inventory_material',
        'beginning_inventory_wip',
        'beginning_inventory_goods',
        'manufacturing_cost',
        'ending_inventory',
        'ending_inventory_material',
        'ending_inventory_wip',
        'ending_inventory_goods',
        'cost_of_sales',
    ]


def test_restructured_pl_has_inventory_breakdown_columns():
    """組換えPLモデルに棚卸高の内訳カラムが存在する"""
    columns = RestructuredPL.__table__.columns.keys()

    for column in [
        'beginning_inventory_material',
        'beginning_inventory_wip',
        'beginning_inventory_goods',
        'ending_inventory_material',
        'ending_inventory_wip',
        'ending_inventory_goods',
    ]:
        assert column in columns


def test_inventory_breakdown_markup_exists_in_templates():
    """PL画面と勘定科目マスタ画面に棚卸高内訳用のUIが存在する"""
    repo_root = Path(__file__).resolve().parent
    account_master = (repo_root / 'app' / 'templates' / 'account_master.html').read_text(encoding='utf-8')
    pl_restructuring = (repo_root / 'app' / 'templates' / 'pl_restructuring.html').read_text(encoding='utf-8')

    assert "key in ['beginning_inventory', 'ending_inventory']" in account_master

    for field in [
        'beginning_inventory_material',
        'beginning_inventory_wip',
        'beginning_inventory_goods',
        'ending_inventory_material',
        'ending_inventory_wip',
        'ending_inventory_goods',
    ]:
        assert f'name="{field}"' in pl_restructuring

    assert 'id="beginning_inventory"' in pl_restructuring
    assert 'id="ending_inventory"' in pl_restructuring
    assert 'data-allow-autofill="true"' in pl_restructuring
    assert "el.dataset.allowAutofill === 'true'" in pl_restructuring
