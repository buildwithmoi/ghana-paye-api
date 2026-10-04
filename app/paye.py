"""Ghana monthly PAYE and employee SSNIT calculator.

Rules: Income Tax (Amendment) Act, 2026 (Act 1178), in force from 1 September 2026,
and SSNIT's insurable-earnings limits for 2026. All amounts are monthly, in GH₵.

Scope: employee SSNIT and PAYE on basic salary plus taxable cash allowances.
Reliefs, bonuses, overtime and benefits in kind are deliberately left out.
"""

from dataclasses import asdict, dataclass
from decimal import ROUND_HALF_UP, Decimal

# PAYE bands as (band width, rate %). None marks the open-ended top band.
PAYE_BANDS = (
    (588.00, 0.0),
    (80.00, 5.0),
    (100.00, 10.0),
    (2_900.00, 17.5),
    (16_000.00, 25.0),
    (30_332.00, 30.0),
    (None, 35.0),
)

SSNIT_EMPLOYEE_RATE = 5.5  # % of insurable earnings
SSNIT_MIN_INSURABLE = 587.79  # contributions are never computed on less than this
SSNIT_MAX_INSURABLE = 69_000.00  # ...or on more than this


def money(amount: float) -> float:
    """Round to pesewas, half up, as payslips do (Python's round() rounds half to even)."""
    return float(Decimal(str(amount)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def ssnit_employee(basic: float) -> float:
    """Employee SSNIT: 5.5% of basic salary, kept within the insurable floor and cap."""
    if basic <= 0:
        return 0.0
    insurable = min(max(basic, SSNIT_MIN_INSURABLE), SSNIT_MAX_INSURABLE)
    return money(insurable * SSNIT_EMPLOYEE_RATE / 100)


def paye(chargeable_income: float) -> float:
    """Progressive PAYE: each slice of income is taxed at its own band's rate."""
    remaining = max(0.0, chargeable_income)
    tax = 0.0
    for width, rate in PAYE_BANDS:
        taxed = remaining if width is None else min(remaining, width)
        tax += taxed * rate / 100
        remaining -= taxed
        if remaining <= 0:
            break
    return money(tax)


@dataclass(frozen=True)
class Payslip:
    basic: float
    allowances: float
    gross: float
    ssnit_employee: float
    chargeable_income: float
    paye: float
    net_pay: float

    def as_dict(self) -> dict:
        return asdict(self)


def calculate(basic: float, allowances: float = 0.0) -> Payslip:
    """Monthly payslip figures. SSNIT comes off before tax, as the law allows."""
    if basic < 0 or allowances < 0:
        raise ValueError("basic and allowances must not be negative")
    gross = money(basic + allowances)
    ssnit = ssnit_employee(basic)
    chargeable = money(max(0.0, gross - ssnit))
    tax = paye(chargeable)
    return Payslip(
        basic=money(basic),
        allowances=money(allowances),
        gross=gross,
        ssnit_employee=ssnit,
        chargeable_income=chargeable,
        paye=tax,
        net_pay=money(gross - ssnit - tax),
    )
