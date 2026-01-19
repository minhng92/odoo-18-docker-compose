# Product Requirement Document (PRD) - eProcurement (ePR)

**Project:** Electronic Purchase Request (ePR) Enterprise  
**Version:** 18.0.1.0.0  
**Status:** Legacy Documentation (Reverse-Engineered)

---

## 1. Business Requirements (BR)

| ID | Requirement Description |
|:---|:---|
| **BR-01** | **Procurement Segregation:** Separate the internal request process (PR) from the external purchasing process (RFQ/PO) to improve control. |
| **BR-02** | **Multi-level Approval:** Implement a dynamic approval matrix based on currency thresholds and department hierarchy. |
| **BR-03** | **Traceability:** Maintain a 1:1 or N:1 link from PR lines to RFQ lines, and from RFQ lines to PO lines. |
| **BR-04** | **Centralized Purchasing:** Allow the Purchasing Department to consolidate multiple internal requests into single vendor negotiations (RFQ merging). |
| **BR-05** | **Audit Trail:** Maintain a history of rejections, approval dates, and actual approvers for compliance. |

---

## 2. Stakeholder Requirements (SR)

### 2.1 Requester (Employees)
- Ability to create draft requests with free-text descriptions (to avoid complex product catalog issues for non-pros).
- Ability to track the real-time status of their requests (Draft -> To Approve -> Approved -> Done).
- Receive clear feedback (Rejection Reasons) if a request is turned down.

### 2.2 Manager (Approver)
- View a consolidated list of requests from their department.
- Approve or Reject requests with a single click from the form or list view.
- Ability to see the estimated total value in the local currency before approving.

### 2.3 Purchasing Officer
- Ability to view all "Approved" requests from across the company.
- Tool to merge multiple PR lines into a single RFQ for a specific vendor.
- Manage price comparisons (RFQ "Received" state) before submitting for final price approval.
- Convert confirmed RFQs into standard Odoo Purchase Orders (PO).

### 2.4 Transition Requirements (TR)
- **TR-01:** Existing internal users must be automatically granted "Requester" access to ensure business continuity.
- **TR-02:** The system must support manual input of "Suggested Vendors" for cases where the requester knows a specific source but is not a master data expert.

---

## 3. Functional Requirements (FR)

### 3.1 Purchase Request (PR) Management
- **FR-01:** Automatic sequence generation for PR references (e.g., PR/2026/0001).
- **FR-02:** Kanban view support for visualizing the PR lifecycle.
- **FR-03:** "Estimated Total" computation at the header level based on line item inputs.
- **FR-04:** "Reset to Draft" functionality to allow requesters to fix and re-submit rejected documents.

### 3.2 RFQ & Merging Workflow
- **FR-05:** **Wizard: Create ePR RFQ:** A dedicated tool to select PR lines and group them by vendor into a new RFQ.
- **FR-06:** Support for "Sent" and "Received" states to track vendor engagement.
- **FR-07:** Price Comparison: Entering actual unit prices from vendor bids into ePR RFQ Lines.

### 3.3 Dynamic Approval Matrix (RFQ)
- **FR-08:** Rule-based approval configuration (`epr.approval.rule`) filtered by Company and Department.
- **FR-09:** **Sequence-based Linearization:** Approvals must happen step-by-step (e.g., Manager first, then Director).
- **FR-10:** Conditional steps: Some approval steps only trigger if the RFQ value exceeds a minimum threshold.
- **FR-11:** **Currency Normalization:** Rules are defined in Company Currency; the system automatically converts foreign currency RFQs for threshold comparison.

### 3.4 Purchase Order (PO) Integration
- **FR-12:** **Wizard: Create PO:** Convert ePR RFQs to Odoo standard `purchase.order`.
- **FR-13:** Header-level Many2many link between PO and source ePR RFQs.
- **FR-14:** Line-level Many2one link from `purchase.order.line` back to `epr.rfq.line`.
- **FR-15:** Smart Buttons on PO to navigate back to PRs and RFQs.

---

## 4. Non-Functional Requirements (NFR)

### 4.1 Security & Access Control
- **NFR-01:** **Record Rules:** Row-level security ensuring Requesters only see their own documents, while Managers see their department.
- **NFR-02:** **Sudo Execution:** Approval logic and history cleanup perform background operations (sudo) to prevent permission blocks for end-users.

### 4.2 Usability & UI
- **NFR-03:** Use of Odoo 18 `<list>` tags instead of deprecated `<tree>` tags.
- **NFR-04:** Implementation of `invisible` and `readonly` attributes for dynamic logic instead of deprecated `attrs`.
- **NFR-05:** Visual status indicators (Decorations) for different document states in list views.

### 4.3 Technical Standards
- **NFR-06:** Full integration with Odoo Mail `chatter` and `activity` mixins for all main documents.
- **NFR-07:** Adherence to OCA coding standards (PEP8, proper imports etc).
