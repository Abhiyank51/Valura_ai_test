import re
from src.core.schemas import SafetyVerdict

class SafetyGuard:
    def __init__(self):
        # Specific allowed queries that might otherwise trigger filters
        self.exact_allowlist = [
            r"what is insider trading", 
            r"why is insider trading illegal", 
            r"explain insider trading risks",
            r"what is a pump and dump scheme",
            r"why are guaranteed returns risky"
        ]

        # Broad educational prefixes
        self.educational_prefixes = [
            r"^what is\b", r"^what are\b", r"^explain\b", r"^difference between\b", 
            r"^how does\b", r"^how should\b", r"^are .* legal\b", r"^role in\b", 
            r"^historical average\b", r"^why are\b", r"^describe the\b", 
            r"^what's the difference\b"
        ]
        
        # Action words that invalidate educational overrides (unless in exact allowlist)
        self.enabling_action_words = [
            r"\buse\b", r"\bexploit\b", r"\bhide\b", r"\bbypass\b", 
            r"\bavoid reporting\b", r"\btrade before\b", r"\bprofit from\b", 
            r"\bmanipulate\b", r"\bcoordinate\b", r"\bstructure deposits\b", 
            r"\blaunder\b", r"\bevade\b", r"\bfake\b", r"\bguarantee\b", 
            r"\bguaranteed way\b", r"\bdouble money\b"
        ]

        self.harmful_patterns = {
            "insider_trading": [
                r"use insider information", r"insider information to trade", 
                r"non-public information", r"material nonpublic information", 
                r"trade before earnings", r"before earnings using inside info",
                r"unannounced acquisition", r"tip about earnings", r"confidential merger", r"earnings before tomorrow",
                r"inside info", r"insider tip", r"trade on confidential", r"non public info", r"material non-public",
                r"earnings leak", r"leaked earnings", r"unreleased earnings", r"insider trading"
            ],
            "market_manipulation": [
                r"pump up", r"coordinated buying", r"wash trade between", r"create volume", r"pump and dump",
                r"pump the price", r"dump after pumping", r"spoof orders", r"fake volume", r"wash trading",
                r"coordinated pump", r"manipulate volume", r"manipulate price"
            ],
            "money_laundering": [
                r"without reporting", r"structure deposits", r"layer my trades", r"hide trading profits",
                r"avoid reporting", r"avoid kyc", r"bypass kyc", r"hide source of funds", r"clean dirty money",
                r"layer transactions", r"structure transactions", r"split deposits", r"avoid detection"
            ],
            "guaranteed_returns": [
                r"guarantee me", r"double in a year", r"100% certain", r"foolproof way",
                r"guaranteed profit", r"risk free profit", r"risk-free profit", r"guaranteed return",
                r"no risk return", r"double my money", r"double money", r"sure shot return", r"guaranteed way"
            ],
            "reckless_advice": [
                r"put all my retirement", r"margin loan to buy", r"entire emergency fund", r"mortgage my house",
                r"all in", r"put everything", r"use emergency fund", r"borrow to invest", r"take a loan to buy",
                r"margin loan", r"retirement savings into"
            ],
            "sanctions_evasion": [r"bypass ofac", r"without it being traced"],
            "fraud": [
                r"fake contract", r"fake statement", r"fake proof of funds", r"forge", r"forged", r"fake kyc"
            ]
        }

    def _is_educational(self, query_lower: str) -> bool:
        has_action_word = any(re.search(pat, query_lower) for pat in self.enabling_action_words)
        query_clean = re.sub(r'[^\w\s]', '', query_lower).strip()

        # Exact allowlist always passes (must match fully and have no action words)
        for pat in self.exact_allowlist:
            # check fullmatch against cleaned query to ignore punctuation
            if re.fullmatch(pat, query_clean) or re.fullmatch(pat, query_lower):
                if not has_action_word:
                    return True

        # Check broad educational prefixes
        is_edu_prefix = any(re.search(pat, query_lower) for pat in self.educational_prefixes)
        
        if is_edu_prefix:
            # But invalidate if it contains enabling action words
            if not has_action_word:
                return True
                
        return False

    def check(self, query: str) -> SafetyVerdict:
        query_lower = query.lower().strip()

        # Check for educational queries first
        if self._is_educational(query_lower):
            return SafetyVerdict(blocked=False, category="safe")

        # Check harmful patterns
        for category, patterns in self.harmful_patterns.items():
            for pat in patterns:
                if re.search(pat, query_lower):
                    message = self._get_message_for_category(category)
                    return SafetyVerdict(blocked=True, category=category, message=message)

        return SafetyVerdict(blocked=False, category="safe")
        
    def _get_message_for_category(self, category: str) -> str:
        messages = {
            "insider_trading": "I can’t help with insider trading or using non-public information to trade. I can help explain legal alternatives such as public-market research, diversification, and risk management.",
            "market_manipulation": "I cannot participate in market manipulation or coordinated trading schemes.",
            "money_laundering": "I cannot provide advice on avoiding reporting requirements or money laundering.",
            "guaranteed_returns": "I cannot guarantee returns. All investments carry risk.",
            "reckless_advice": "I cannot provide reckless financial advice or encourage over-leveraging.",
            "sanctions_evasion": "I cannot assist with evading sanctions.",
            "fraud": "I cannot assist with fraudulent activities."
        }
        return messages.get(category, "I cannot fulfill this request due to safety policies.")

guard = SafetyGuard()

def check(query: str) -> SafetyVerdict:
    return guard.check(query)
