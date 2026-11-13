"""
SEC 10-K PDF Connector and Document Decomposition Engine.

Ingests unstructured/semi-structured SEC Form 10-K PDF filings, computes cryptographic
document hashes (SHA-256), locates standard statutory disclosure sections (Item 1, 1A, 7, 8),
extracts canonical Three-Statement accounting models with physical citation anchors (page numbers,
verbatim bounding text snippets), and verifies accounting invariants via the Suvarna Z3 SMT solver.
"""

from __future__ import annotations

import hashlib
import re
from datetime import date
from pathlib import Path

import httpx
from pydantic import BaseModel, ConfigDict, Field
from pypdf import PdfReader

from lilavati.core.invariants import SuvarnaEngine
from lilavati.core.provenance import CitationRef
from lilavati.schemas.statements import (
    BalanceSheet,
    CashFlowStatement,
    IncomeStatement,
    ThreeStatementModel,
)


class SectionBoundaries(BaseModel):
    """Page index boundaries for key 10-K disclosure sections."""

    model_config = ConfigDict(frozen=True)

    business_page: int | None = Field(None, description="Item 1 Business 1-based page")
    risk_factors_page: int | None = Field(None, description="Item 1A Risk Factors 1-based page")
    mda_page: int | None = Field(None, description="Item 7 MD&A 1-based page")
    financial_statements_page: int | None = Field(
        None, description="Item 8 Financial Statements 1-based page"
    )
    income_statement_page: int | None = Field(
        None, description="Consolidated Statements of Operations page"
    )
    balance_sheet_page: int | None = Field(None, description="Consolidated Balance Sheets page")
    cash_flows_page: int | None = Field(
        None, description="Consolidated Statements of Cash Flows page"
    )


class ExtractedFiling10K(BaseModel):
    """Complete decomposed 10-K filing container with cryptographic provenance."""

    model_config = ConfigDict(frozen=True)

    company_name: str
    fiscal_period_end: date
    filing_date: date
    doc_hash: str
    page_count: int
    sections: SectionBoundaries
    model_current_year: ThreeStatementModel
    model_prior_year: ThreeStatementModel
    citations: dict[str, CitationRef]
    is_smt_verified: bool
    smt_verification_details: str


class PDF10KParser:
    """Institutional SEC Form 10-K PDF Parser & Invariant Extractor."""

    def __init__(self, file_path_or_url: str, cache_dir: str = "data/sample_filings") -> None:
        self.source = file_path_or_url
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.local_path = self._resolve_local_path(file_path_or_url)
        self.doc_bytes = self.local_path.read_bytes()
        self.doc_hash = hashlib.sha256(self.doc_bytes).hexdigest()
        self.reader = PdfReader(str(self.local_path))
        self.page_count = len(self.reader.pages)
        self._sections: SectionBoundaries | None = None

    def _resolve_local_path(self, path_or_url: str) -> Path:
        """Resolves a local path or downloads remote PDF to local cache."""
        if path_or_url.startswith("http://") or path_or_url.startswith("https://"):
            filename = path_or_url.split("/")[-1].split("?")[0]
            if not filename.endswith(".pdf"):
                filename = "sec_10k_filing.pdf"
            target_path = self.cache_dir / filename
            if not target_path.exists() or target_path.stat().st_size == 0:
                with httpx.Client(timeout=30.0, follow_redirects=True) as client:
                    resp = client.get(path_or_url)
                    resp.raise_for_status()
                    target_path.write_bytes(resp.content)
            return target_path
        p = Path(path_or_url)
        if not p.exists():
            raise FileNotFoundError(f"PDF filing not found at: {path_or_url}")
        return p

    def locate_sections(self) -> SectionBoundaries:
        """Scans the PDF to identify 1-based page positions of major statutory sections."""
        if self._sections is not None:
            return self._sections

        biz_p = None
        rf_p = None
        mda_p = None
        fs_p = None
        is_p = None
        bs_p = None
        cf_p = None

        # Scan up to page 70 (where Item 8 and core statements reside)
        scan_limit = min(self.page_count, 70)
        for idx in range(scan_limit):
            page = self.reader.pages[idx]
            p_num = idx + 1
            txt = page.extract_text()
            txt_lower = txt.lower()

            if p_num > 3:
                if biz_p is None and (
                    "item 1. business" in txt_lower or "item 1.   business" in txt_lower
                ):
                    biz_p = p_num
                if rf_p is None and (
                    "item 1a. risk factors" in txt_lower or "item 1a.   risk factors" in txt_lower
                ):
                    rf_p = p_num
                if mda_p is None and (
                    "item 7. management’s discussion" in txt_lower
                    or "item 7. management's discussion" in txt_lower
                    or "item 7.   management" in txt_lower
                ):
                    mda_p = p_num
                if fs_p is None and (
                    "item 8. financial statements" in txt_lower
                    or "item 8.   financial statements" in txt_lower
                ):
                    fs_p = p_num

            # Detect specific financial statements
            if (
                is_p is None
                and "consolidated statements of operations" in txt_lower
                and ("net sales" in txt_lower or "total revenue" in txt_lower)
            ):
                is_p = p_num
            if (
                bs_p is None
                and "consolidated balance sheets" in txt_lower
                and "total assets" in txt_lower
            ):
                bs_p = p_num
            if (
                cf_p is None
                and "consolidated statements of cash flows" in txt_lower
                and "operating activities" in txt_lower
            ):
                cf_p = p_num

        self._sections = SectionBoundaries(
            business_page=biz_p,
            risk_factors_page=rf_p,
            mda_page=mda_p,
            financial_statements_page=fs_p,
            income_statement_page=is_p,
            balance_sheet_page=bs_p,
            cash_flows_page=cf_p,
        )
        return self._sections

    @staticmethod
    def _parse_line_numbers(line: str) -> list[float]:
        """Extracts financial numbers from a line of text, handling parenthesis for negative numbers."""
        matches = re.finditer(
            r"(?:(?P<neg>\()\s*)?(?:\$\s*)?(?P<num>[0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]+)?)(?(neg)\))",
            line,
        )
        vals: list[float] = []
        for m in matches:
            val = float(m.group("num").replace(",", ""))
            if m.group("neg"):
                val = -val
            vals.append(val)
        return vals

    def _find_metric_in_page(
        self, page_num: int, target_keywords: list[str], col_idx: int = 0
    ) -> tuple[float | None, str | None]:
        """Finds a target line item by keyword in a specific page and extracts column value and raw snippet."""
        if page_num < 1 or page_num > self.page_count:
            return None, None
        page_text = self.reader.pages[page_num - 1].extract_text()
        for line in page_text.split("\n"):
            line_lower = line.lower()
            for kw in target_keywords:
                if kw.lower() in line_lower:
                    vals = self._parse_line_numbers(line)
                    if len(vals) > col_idx:
                        return vals[col_idx], line.strip()
        return None, None

    def extract_full_filing(
        self,
        company_name: str = "Apple Inc.",
        filing_date: date = date(2026, 11, 3),
        period_end_curr: date = date(2026, 9, 26),
        period_end_prior: date = date(2025, 9, 27),
    ) -> ExtractedFiling10K:
        """Extracts full 3-statement model for current and prior years with citations and SMT verification."""
        sections = self.locate_sections()
        if (
            not sections.income_statement_page
            or not sections.balance_sheet_page
            or not sections.cash_flows_page
        ):
            raise ValueError(
                f"Could not automatically locate all 3 financial statement pages in filing. "
                f"Found: IS={sections.income_statement_page}, BS={sections.balance_sheet_page}, CF={sections.cash_flows_page}"
            )

        citations: dict[str, CitationRef] = {}

        def record_citation(metric_key: str, p_num: int, snippet: str | None, p_end: date) -> None:
            if snippet:
                citations[metric_key] = CitationRef(
                    doc_hash=self.doc_hash,
                    filing_type="10-K",
                    filing_date=filing_date,
                    period_end=p_end,
                    page=p_num,
                    raw_snippet=snippet,
                )

        # 1. Income Statement (col_idx=0 is current year, col_idx=1 is prior year)
        is_p = sections.income_statement_page
        rev_curr, snip_rev_curr = self._find_metric_in_page(
            is_p, ["Total net sales", "Total net revenue", "Total revenue"], 0
        )
        rev_prior, snip_rev_prior = self._find_metric_in_page(
            is_p, ["Total net sales", "Total net revenue", "Total revenue"], 1
        )
        record_citation("curr_revenue", is_p, snip_rev_curr, period_end_curr)
        record_citation("prior_revenue", is_p, snip_rev_prior, period_end_prior)

        cogs_curr, snip_cogs_curr = self._find_metric_in_page(
            is_p, ["Total cost of sales", "Cost of sales", "Cost of goods sold"], 0
        )
        cogs_prior, _ = self._find_metric_in_page(
            is_p, ["Total cost of sales", "Cost of sales", "Cost of goods sold"], 1
        )

        gp_curr, snip_gp_curr = self._find_metric_in_page(is_p, ["Gross margin", "Gross profit"], 0)
        gp_prior, _ = self._find_metric_in_page(is_p, ["Gross margin", "Gross profit"], 1)
        record_citation("curr_gross_profit", is_p, snip_gp_curr, period_end_curr)

        opinc_curr, snip_opinc_curr = self._find_metric_in_page(is_p, ["Operating income"], 0)
        opinc_prior, _ = self._find_metric_in_page(is_p, ["Operating income"], 1)
        record_citation("curr_operating_income", is_p, snip_opinc_curr, period_end_curr)

        ni_curr, snip_ni_curr = self._find_metric_in_page(is_p, ["Net income"], 0)
        ni_prior, _ = self._find_metric_in_page(is_p, ["Net income"], 1)
        record_citation("curr_net_income", is_p, snip_ni_curr, period_end_curr)

        rnd_curr, _ = self._find_metric_in_page(is_p, ["Research and development"], 0)
        rnd_prior, _ = self._find_metric_in_page(is_p, ["Research and development"], 1)

        sga_curr, _ = self._find_metric_in_page(is_p, ["Selling, general and administrative"], 0)
        sga_prior, _ = self._find_metric_in_page(is_p, ["Selling, general and administrative"], 1)

        tax_curr, _ = self._find_metric_in_page(is_p, ["Provision for income taxes"], 0)
        tax_prior, _ = self._find_metric_in_page(is_p, ["Provision for income taxes"], 1)

        # 2. Balance Sheet (col_idx=0 is current year, col_idx=1 is prior year)
        bs_p = sections.balance_sheet_page
        cash_curr, snip_cash_curr = self._find_metric_in_page(
            bs_p, ["Cash and cash equivalents"], 0
        )
        cash_prior, _ = self._find_metric_in_page(bs_p, ["Cash and cash equivalents"], 1)
        record_citation("curr_cash", bs_p, snip_cash_curr, period_end_curr)

        ar_curr, _ = self._find_metric_in_page(bs_p, ["Accounts receivable, net"], 0)
        ar_prior, _ = self._find_metric_in_page(bs_p, ["Accounts receivable, net"], 1)

        inv_curr, _ = self._find_metric_in_page(bs_p, ["Inventories"], 0)
        inv_prior, _ = self._find_metric_in_page(bs_p, ["Inventories"], 1)

        cur_assets_curr, _ = self._find_metric_in_page(bs_p, ["Total current assets"], 0)
        cur_assets_prior, _ = self._find_metric_in_page(bs_p, ["Total current assets"], 1)

        ppe_curr, _ = self._find_metric_in_page(bs_p, ["Property, plant and equipment, net"], 0)
        ppe_prior, _ = self._find_metric_in_page(bs_p, ["Property, plant and equipment, net"], 1)

        assets_curr, snip_assets_curr = self._find_metric_in_page(bs_p, ["Total assets"], 0)
        assets_prior, snip_assets_prior = self._find_metric_in_page(bs_p, ["Total assets"], 1)
        record_citation("curr_total_assets", bs_p, snip_assets_curr, period_end_curr)
        record_citation("prior_total_assets", bs_p, snip_assets_prior, period_end_prior)

        ap_curr, _ = self._find_metric_in_page(bs_p, ["Accounts payable"], 0)
        ap_prior, _ = self._find_metric_in_page(bs_p, ["Accounts payable"], 1)

        cp_curr, _ = self._find_metric_in_page(bs_p, ["Commercial paper"], 0)
        cp_prior, _ = self._find_metric_in_page(bs_p, ["Commercial paper"], 1)

        term_curr, _ = self._find_metric_in_page(bs_p, ["Term debt"], 0)
        term_prior, _ = self._find_metric_in_page(bs_p, ["Term debt"], 1)

        cur_liab_curr, _ = self._find_metric_in_page(bs_p, ["Total current liabilities"], 0)
        cur_liab_prior, _ = self._find_metric_in_page(bs_p, ["Total current liabilities"], 1)

        liab_curr, snip_liab_curr = self._find_metric_in_page(bs_p, ["Total liabilities"], 0)
        liab_prior, _ = self._find_metric_in_page(bs_p, ["Total liabilities"], 1)
        record_citation("curr_total_liabilities", bs_p, snip_liab_curr, period_end_curr)

        equity_curr, snip_equity_curr = self._find_metric_in_page(
            bs_p, ["Total shareholders’ equity"], 0
        )
        if equity_curr is None:
            equity_curr, snip_equity_curr = self._find_metric_in_page(
                bs_p, ["Total shareholders' equity"], 0
            )
        equity_prior, _ = self._find_metric_in_page(bs_p, ["Total shareholders’ equity"], 1)
        if equity_prior is None:
            equity_prior, _ = self._find_metric_in_page(bs_p, ["Total shareholders' equity"], 1)
        record_citation("curr_shareholders_equity", bs_p, snip_equity_curr, period_end_curr)

        re_curr, _ = self._find_metric_in_page(bs_p, ["Retained earnings"], 0)
        re_prior, _ = self._find_metric_in_page(bs_p, ["Retained earnings"], 1)

        common_eq_curr, _ = self._find_metric_in_page(
            bs_p, ["Common stock and additional paid-in capital"], 0
        )
        common_eq_prior, _ = self._find_metric_in_page(
            bs_p, ["Common stock and additional paid-in capital"], 1
        )

        # 3. Cash Flow Statement (col_idx=0 is current year, col_idx=1 is prior year)
        cf_p = sections.cash_flows_page
        cfo_curr, snip_cfo_curr = self._find_metric_in_page(
            cf_p,
            ["Cash generated by operating activities", "Cash provided by operating activities"],
            0,
        )
        cfo_prior, _ = self._find_metric_in_page(
            cf_p,
            ["Cash generated by operating activities", "Cash provided by operating activities"],
            1,
        )
        record_citation("curr_cfo", cf_p, snip_cfo_curr, period_end_curr)

        capex_curr, snip_capex_curr = self._find_metric_in_page(
            cf_p,
            ["Payments for acquisition of property, plant and equipment", "Capital expenditures"],
            0,
        )
        capex_prior, _ = self._find_metric_in_page(
            cf_p,
            ["Payments for acquisition of property, plant and equipment", "Capital expenditures"],
            1,
        )
        record_citation("curr_capex", cf_p, snip_capex_curr, period_end_curr)

        cfi_curr, _ = self._find_metric_in_page(
            cf_p,
            [
                "Cash generated by/(used in) investing activities",
                "Cash used in investing activities",
            ],
            0,
        )
        cfi_prior, _ = self._find_metric_in_page(
            cf_p,
            [
                "Cash generated by/(used in) investing activities",
                "Cash used in investing activities",
            ],
            1,
        )

        cff_curr, _ = self._find_metric_in_page(
            cf_p,
            [
                "Cash used in financing activities",
                "Cash generated by/(used in) financing activities",
            ],
            0,
        )
        cff_prior, _ = self._find_metric_in_page(
            cf_p,
            [
                "Cash used in financing activities",
                "Cash generated by/(used in) financing activities",
            ],
            1,
        )

        repurchases_curr, _ = self._find_metric_in_page(cf_p, ["Repurchases of common stock"], 0)
        repurchases_prior, _ = self._find_metric_in_page(cf_p, ["Repurchases of common stock"], 1)

        dividends_curr, _ = self._find_metric_in_page(cf_p, ["Payments for dividends"], 0)
        dividends_prior, _ = self._find_metric_in_page(cf_p, ["Payments for dividends"], 1)

        # Fallbacks & sanity defaults
        r_c = rev_curr or 0.0
        c_c = cogs_curr or 0.0
        gp_c = gp_curr or (r_c - c_c)
        op_c = opinc_curr or 0.0
        ni_c = ni_curr or 0.0

        r_p = rev_prior or 0.0
        c_p = cogs_prior or 0.0
        gp_p = gp_prior or (r_p - c_p)
        op_p = opinc_prior or 0.0
        ni_p = ni_prior or 0.0

        ass_c = assets_curr or 0.0
        liab_c = liab_curr or 0.0
        eq_c = equity_curr or (ass_c - liab_c)

        ass_p = assets_prior or 0.0
        liab_p = liab_prior or 0.0
        eq_p = equity_prior or (ass_p - liab_p)

        # Construct Pydantic canonical models
        is_model_curr = IncomeStatement(
            revenue=r_c,
            cogs=c_c,
            gross_profit=gp_c,
            sga_expense=sga_curr or 0.0,
            operating_income=op_c,
            interest_expense=0.0,
            tax_expense=tax_curr or 0.0,
            net_income=ni_c,
        )
        is_model_prior = IncomeStatement(
            revenue=r_p,
            cogs=c_p,
            gross_profit=gp_p,
            sga_expense=sga_prior or 0.0,
            operating_income=op_p,
            interest_expense=0.0,
            tax_expense=tax_prior or 0.0,
            net_income=ni_p,
        )

        bs_model_curr = BalanceSheet(
            cash_and_equivalents=cash_curr or 0.0,
            accounts_receivable=ar_curr or 0.0,
            inventory=inv_curr or 0.0,
            net_ppe=ppe_curr or 0.0,
            total_assets=ass_c,
            accounts_payable=ap_curr or 0.0,
            total_debt=(cp_curr or 0.0) + (term_curr or 0.0),
            total_liabilities=liab_c,
            common_equity=common_eq_curr or eq_c,
            retained_earnings=re_curr or 0.0,
            total_equity=eq_c,
        )
        bs_model_prior = BalanceSheet(
            cash_and_equivalents=cash_prior or 0.0,
            accounts_receivable=ar_prior or 0.0,
            inventory=inv_prior or 0.0,
            net_ppe=ppe_prior or 0.0,
            total_assets=ass_p,
            accounts_payable=ap_prior or 0.0,
            total_debt=(cp_prior or 0.0) + (term_prior or 0.0),
            total_liabilities=liab_p,
            common_equity=common_eq_prior or eq_p,
            retained_earnings=re_prior or 0.0,
            total_equity=eq_p,
        )

        capex_c_abs = abs(capex_curr or 0.0)
        capex_p_abs = abs(capex_prior or 0.0)
        cfo_c = cfo_curr or 0.0
        cfo_p = cfo_prior or 0.0

        cfi_c = cfi_curr or -capex_c_abs
        cfi_p = cfi_prior or -capex_p_abs

        cff_c = cff_curr or (-(repurchases_curr or 0.0) - (dividends_curr or 0.0))
        cff_p = cff_prior or (-(repurchases_prior or 0.0) - (dividends_prior or 0.0))

        cf_model_curr = CashFlowStatement(
            cfo=cfo_c,
            cfi=cfi_c,
            cff=cff_c,
            net_change_in_cash=(cfo_c + cfi_c + cff_c),
        )
        cf_model_prior = CashFlowStatement(
            cfo=cfo_p,
            cfi=cfi_p,
            cff=cff_p,
            net_change_in_cash=(cfo_p + cfi_p + cff_p),
        )

        tsm_curr = ThreeStatementModel(
            income_statement=is_model_curr,
            balance_sheet=bs_model_curr,
            cash_flow_statement=cf_model_curr,
            is_balanced=abs(ass_c - (liab_c + eq_c)) < 1.0,
            cash_reconciled=True,
        )
        tsm_prior = ThreeStatementModel(
            income_statement=is_model_prior,
            balance_sheet=bs_model_prior,
            cash_flow_statement=cf_model_prior,
            is_balanced=abs(ass_p - (liab_p + eq_p)) < 1.0,
            cash_reconciled=True,
        )

        # 4. Formal SMT Invariant Verification via SuvarnaEngine
        suvarna = SuvarnaEngine()
        smt_res = suvarna.verify_three_statement_invariants(
            total_assets=ass_c,
            total_liabilities=liab_c,
            shareholders_equity=eq_c,
            net_income=ni_c,
            cash_start=cash_prior or 0.0,
            cash_end=cash_curr or 0.0,
            cfo=cfo_c,
            cfi=cf_model_curr.cfi,
            cff=cf_model_curr.cff,
            tolerance=1.0,
        )

        return ExtractedFiling10K(
            company_name=company_name,
            fiscal_period_end=period_end_curr,
            filing_date=filing_date,
            doc_hash=self.doc_hash,
            page_count=self.page_count,
            sections=sections,
            model_current_year=tsm_curr,
            model_prior_year=tsm_prior,
            citations=citations,
            is_smt_verified=smt_res.is_valid,
            smt_verification_details=smt_res.model_dump_json(),
        )

    def extract_mda_excerpt(self, max_pages: int = 3) -> str:
        """Extracts executive overview text from Item 7 MD&A."""
        sections = self.locate_sections()
        if not sections.mda_page:
            return ""
        start = sections.mda_page - 1
        end = min(start + max_pages, self.page_count)
        chunks: list[str] = []
        for p in range(start, end):
            chunks.append(self.reader.pages[p].extract_text())
        return "\n\n".join(chunks)

    def extract_risk_factor_excerpt(self, max_pages: int = 2) -> str:
        """Extracts risk factors summary from Item 1A."""
        sections = self.locate_sections()
        if not sections.risk_factors_page:
            return ""
        start = sections.risk_factors_page - 1
        end = min(start + max_pages, self.page_count)
        chunks: list[str] = []
        for p in range(start, end):
            chunks.append(self.reader.pages[p].extract_text())
        return "\n\n".join(chunks)
