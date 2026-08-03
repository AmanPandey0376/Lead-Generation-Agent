import re
import logging
from typing import List, Dict, Any, Set

logger = logging.getLogger(__name__)

def validate_leads(leads: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Validates a batch of extracted leads based on rules.
    Rejects invalid leads and returns only the clean leads.
    """
    seen_companies: Set[str] = set()
    validated_leads: List[Dict[str, Any]] = []

    for lead in leads:
        company = lead.get("company") or ""
        website = lead.get("website") or ""

        # 1. Company name missing
        if not company or company.strip() == "":
            logger.info("Lead Validation: Rejected lead (Company Name missing)")
            continue

        # 2. Website missing
        if not website or website.strip() == "":
            logger.info(f"Lead Validation: Rejected lead for '{company}' (Website missing)")
            continue

        # 3. Reject duplicate companies in the current batch (case-insensitive)
        company_key = company.strip().lower()
        if company_key in seen_companies:
            logger.info(f"Lead Validation: Rejected lead for '{company}' (Duplicate company in current batch)")
            continue

        # Check placeholder company name
        company_lower = company.lower()
        if (
            "placeholder" in company_lower or
            "unknown" in company_lower or
            "test company" in company_lower or
            "dummy" in company_lower or
            company_lower.strip() == "n/a"
        ):
            logger.info(f"Lead Validation: Rejected lead for '{company}' (Placeholder company name)")
            continue

        # 4. Invalid domain check
        domain = website.strip().lower()
        # Normalize domain by stripping protocols and subdomains
        domain = re.sub(r'^(https?://)?(www\.)?', '', domain)
        # Remove query params and paths
        domain = domain.split('/')[0]

        if (
            "." not in domain or
            domain.startswith(".") or
            domain.endswith(".") or
            " " in domain or
            len(domain) < 4
        ):
            logger.info(f"Lead Validation: Rejected lead for '{company}' (Invalid domain '{website}')")
            continue

        # Check placeholder website
        website_lower = website.lower()
        if (
            "example.com" in website_lower or
            "test.com" in website_lower or
            "sample.com" in website_lower or
            "dummy.com" in website_lower or
            "placeholder" in website_lower
        ):
            logger.info(f"Lead Validation: Rejected lead for '{company}' (Placeholder website '{website}')")
            continue

        # Reject emails containing placeholders
        email = lead.get("email") or ""
        if email:
            email_lower = email.strip().lower()
            if (
                "example.com" in email_lower or
                "test.com" in email_lower or
                "sample.com" in email_lower or
                "dummy.com" in email_lower or
                "placeholder" in email_lower or
                "email@" in email_lower or
                "xxx" in email_lower or
                email_lower == "n/a"
            ):
                # Clear invalid email instead of rejecting the whole lead
                lead["email"] = ""

        # Clean optional fields containing placeholder strings
        phone = lead.get("phone") or ""
        if phone:
            phone_lower = phone.strip().lower()
            if (
                "xxx" in phone_lower or
                "placeholder" in phone_lower or
                "12345" in phone_lower or
                "000000" in phone_lower or
                phone_lower == "n/a"
            ):
                lead["phone"] = ""

        linkedin = lead.get("linkedIn") or lead.get("linkedin") or ""
        if linkedin:
            li_lower = linkedin.strip().lower()
            if (
                "placeholder" in li_lower or
                "linkedin.com/in/xxx" in li_lower or
                "linkedin.com/company/xxx" in li_lower or
                li_lower == "n/a"
            ):
                if "linkedIn" in lead:
                    lead["linkedIn"] = ""
                if "linkedin" in lead:
                    lead["linkedin"] = ""

        # 5. Only save leads that have at least one: Website, Phone Number, Business Email, LinkedIn Page
        has_contact_channel = bool(
            (lead.get("website") and lead.get("website").strip() != "") or
            (lead.get("phone") and lead.get("phone").strip() != "") or
            (lead.get("email") and lead.get("email").strip() != "") or
            ((lead.get("linkedIn") or lead.get("linkedin")) and (lead.get("linkedIn") or lead.get("linkedin")).strip() != "")
        )

        if not has_contact_channel:
            logger.info(f"Lead Validation: Rejected lead for '{company}' (No valid contact channels)")
            continue

        seen_companies.add(company_key)
        validated_leads.append(lead)

    return validated_leads
