import pytest

from app.paye import calculate, money, paye, ssnit_employee


@pytest.mark.parametrize(
    ("chargeable", "expected"),
    [
        (0, 0.00),
        (588, 0.00),  # top of the tax-free band
        (589, 0.05),  # first cedi taxed at 5%
        (668, 4.00),  # top of the 5% band: 80 x 5%
        (768, 14.00),  # top of the 10% band: 4 + 100 x 10%
        (4_725, 785.75),  # 14 + 2,900 x 17.5% + 1,057 x 25%
        (50_000, 13_621.10),  # top of the 30% band
        (96_205, 29_792.85),  # 13,621.10 + 46,205 x 35%
    ],
)
def test_paye_bands(chargeable, expected):
    assert paye(chargeable) == expected


@pytest.mark.parametrize(
    ("basic", "expected"),
    [
        (0, 0.00),
        (500, 32.33),  # below the floor: charged on GH₵ 587.79
        (5_000, 275.00),
        (100_000, 3_795.00),  # above the cap: charged on GH₵ 69,000
    ],
)
def test_ssnit_floor_and_cap(basic, expected):
    assert ssnit_employee(basic) == expected


def test_full_payslip():
    slip = calculate(basic=5_000)
    assert slip.ssnit_employee == 275.00
    assert slip.chargeable_income == 4_725.00
    assert slip.paye == 785.75
    assert slip.net_pay == 3_939.25


def test_allowances_are_taxed_but_not_ssnit_insurable():
    slip = calculate(basic=5_000, allowances=1_000)
    assert slip.gross == 6_000.00
    assert slip.ssnit_employee == 275.00  # SSNIT is on basic only
    assert slip.chargeable_income == 5_725.00
    assert slip.paye == 1_035.75  # the extra 1,000 falls in the 25% band


def test_net_pay_adds_up():
    slip = calculate(basic=12_345.67, allowances=890.12)
    assert money(slip.ssnit_employee + slip.paye + slip.net_pay) == slip.gross


def test_rounds_half_up():
    assert money(0.125) == 0.13


def test_negative_amounts_rejected():
    with pytest.raises(ValueError):
        calculate(basic=-1)
