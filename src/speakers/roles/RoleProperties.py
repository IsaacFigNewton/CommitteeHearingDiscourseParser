from typing import Optional
from dataclasses import dataclass

@dataclass
class RoleProperties:
    # is speaker a committee member?
    is_committee_member:    Optional[bool]
    # is speaker an author of the current bill?
    is_bill_author:         Optional[bool]