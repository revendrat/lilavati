"""
Canonical Pydantic V2 Schemas for Three-Statement Financial Modeling.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class IncomeStatement(BaseModel):
    """Canonical Income Statement line items."""

    model_config = ConfigDict(frozen=True)

    revenue: float = Field(..., description="Top-line gross revenue")
    cogs: float = Field(..., description="Cost of goods sold")
    gross_profit: float = Field(..., description="Revenue - COGS")
    sga_expense: float = Field(..., description="Selling, general, and administrative expenses")
    operating_income: float = Field(..., description="Gross profit - SG&A (EBIT)")
    interest_expense: float = Field(default=0.0, description="Gross interest obligations")
    tax_expense: float = Field(default=0.0, description="Income taxes")
    net_income: float = Field(..., description="Bottom-line earnings available to common equity")


class CashFlowStatement(BaseModel):
    """Canonical Cash Flow Statement line items."""

    model_config = ConfigDict(frozen=True)

    cfo: float = Field(..., description="Cash flow from operating activities")
    cfi: float = Field(
        ..., description="Cash flow from investing activities (typically negative for capex)"
    )
    cff: float = Field(
        ..., description="Cash flow from financing activities (debt issuance, dividends)"
    )
    net_change_in_cash: float = Field(..., description="CFO + CFI + CFF")


class BalanceSheet(BaseModel):
    """Canonical Balance Sheet line items."""

    model_config = ConfigDict(frozen=True)

    cash_and_equivalents: float = Field(
        ..., description="Liquid cash and cash equivalents (cash plug)"
    )
    accounts_receivable: float = Field(default=0.0, description="Uncollected customer billings")
    inventory: float = Field(default=0.0, description="Inventory on hand")
    net_ppe: float = Field(..., description="Property, plant, and equipment net of depreciation")
    total_assets: float = Field(
        ..., description="Sum of all liquid, current, and non-current assets"
    )

    accounts_payable: float = Field(default=0.0, description="Short-term supplier obligations")
    total_debt: float = Field(..., description="Short-term and long-term interest-bearing debt")
    total_liabilities: float = Field(
        ..., description="Sum of all operational and financial liabilities"
    )

    retained_earnings: float = Field(..., description="Cumulative retained profits")
    common_equity: float = Field(
        ..., description="Par value of shares + additional paid-in capital"
    )
    total_equity: float = Field(..., description="Total shareholders' equity")


class ThreeStatementModel(BaseModel):
    """Fully integrated, reconciled Three-Statement Model for a single fiscal period."""

    model_config = ConfigDict(frozen=True)

    income_statement: IncomeStatement
    cash_flow_statement: CashFlowStatement
    balance_sheet: BalanceSheet
    is_balanced: bool = Field(..., description="True if Assets == Liabilities + Equity")
    cash_reconciled: bool = Field(
        ..., description="True if Ending Cash == Starting Cash + Net Cash Flow"
    )
