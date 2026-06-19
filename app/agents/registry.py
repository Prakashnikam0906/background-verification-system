# app/agents/registry.py

from app.agents.identity_agents import (
    NameValidationAgent,
    DOBVerificationAgent,
    AddressVerificationAgent,
    GovernmentIDAgent,
    AddressHistoryAgent,
)
from app.agents.criminal_agents import (
    FederalCriminalCheckAgent,
    StateCriminalCheckAgent,
    CountyRecordsAgent,
    SexOffenderRegistryAgent,
    InterpolAgent,
)
from app.agents.financial_agents import (
    CreditVerificationAgent,
    FraudDetectionAgent,
    SanctionsScreeningAgent,
    BankruptcyCheckAgent,
    PEPScreeningAgent,
    AdverseMediaAgent,
)


# all 16 agents - instantiated once (singleton style)
ALL_AGENTS = {
    # identity
    "NameValidationAgent":             NameValidationAgent(),
    "DOBVerificationAgent":            DOBVerificationAgent(),
    "AddressVerificationAgent":        AddressVerificationAgent(),
    "GovernmentIDAgent":               GovernmentIDAgent(),
    "AddressHistoryAgent":             AddressHistoryAgent(),
    # criminal
    "FederalCriminalCheckAgent":       FederalCriminalCheckAgent(),
    "StateCriminalCheckAgent":         StateCriminalCheckAgent(),
    "CountyRecordsAgent":              CountyRecordsAgent(),
    "SexOffenderRegistryAgent":        SexOffenderRegistryAgent(),
    "InterpolAgent":                   InterpolAgent(),
    # financial
    "CreditVerificationAgent":         CreditVerificationAgent(),
    "FraudDetectionAgent":             FraudDetectionAgent(),
    "SanctionsScreeningAgent":         SanctionsScreeningAgent(),
    "BankruptcyCheckAgent":            BankruptcyCheckAgent(),
    "PEPScreeningAgent":               PEPScreeningAgent(),
    "AdverseMediaAgent":               AdverseMediaAgent(),
}

# category groupings
CATEGORY_MAP = {
    "identity": [
        "NameValidationAgent",
        "DOBVerificationAgent",
        "AddressVerificationAgent",
        "GovernmentIDAgent",
        "AddressHistoryAgent",
    ],
    "criminal": [
        "FederalCriminalCheckAgent",
        "StateCriminalCheckAgent",
        "CountyRecordsAgent",
        "SexOffenderRegistryAgent",
        "InterpolAgent",
    ],
    "financial": [
        "CreditVerificationAgent",
        "FraudDetectionAgent",
        "SanctionsScreeningAgent",
        "BankruptcyCheckAgent",
        "PEPScreeningAgent",
        "AdverseMediaAgent",
    ],
}

# feedback keyword → agents to re-run
# this is how selective re-execution works
FEEDBACK_KEYWORDS = {
    "address":       ["AddressVerificationAgent", "AddressHistoryAgent"],
    "name":          ["NameValidationAgent"],
    "dob":           ["DOBVerificationAgent"],
    "date of birth": ["DOBVerificationAgent"],
    "age":           ["DOBVerificationAgent"],
    "id":            ["GovernmentIDAgent"],
    "passport":      ["GovernmentIDAgent"],
    "license":       ["GovernmentIDAgent"],
    "identity":      CATEGORY_MAP["identity"],
    "criminal":      CATEGORY_MAP["criminal"],
    "federal":       ["FederalCriminalCheckAgent"],
    "state":         ["StateCriminalCheckAgent"],
    "county":        ["CountyRecordsAgent"],
    "sex offender":  ["SexOffenderRegistryAgent"],
    "interpol":      ["InterpolAgent"],
    "financial":     CATEGORY_MAP["financial"],
    "credit":        ["CreditVerificationAgent"],
    "fraud":         ["FraudDetectionAgent"],
    "sanctions":     ["SanctionsScreeningAgent"],
    "ofac":          ["SanctionsScreeningAgent"],
    "bankruptcy":    ["BankruptcyCheckAgent"],
    "pep":           ["PEPScreeningAgent"],
    "political":     ["PEPScreeningAgent"],
    "media":         ["AdverseMediaAgent"],
    "news":          ["AdverseMediaAgent"],
}
