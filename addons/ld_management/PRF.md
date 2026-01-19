# Product Requirement Framework (PRF) - L&D Management System

**Project:** Learning & Development (L&D) Management System  
**Version:** 1.0.0  
**Status:** In-Development  

---

## 1. Section 1: Core User Requirements (As Specified)

### 1.1 Business Requirements (BR)
| ID | Requirement Description |
|:---|:---|
| **BR-01** | **Training Request Management:** Streamline the end-to-end process of identifying and requesting training needs. |
| **BR-02** | **Targeted Distribution:** Ensure courses are assigned and visible only to relevant audiences (Include/Exclude logic). |
| **BR-03** | **Cost Control:** Tracking and management of internal and external training expenditures. |
| **BR-04** | **Skill Linkage:** Integrate training outcomes directly with Employee Skill Profiles (`hr.skill`). |
| **BR-05** | **Certification Management:** Tracking validity of certifications with automated expiration notifications. |

### 1.2 Strategic & System Requirements (SR)
| ID | Requirement Description |
|:---|:---|
| **SR-01** | **Advanced Filtering:** Complex learner selection tools for Officers to manage bulk enrollments and registration approvals. |
| **SR-02** | **Self-Service Portal:** User-friendly interface for employees to browse allowed courses and perform self-registration. |
| **SR-03** | **HoD Dashboards:** Visualization for Heads of Department to monitor team learning progress and associated costs. |
| **SR-04** | **Resource Booking:** Management of training rooms, equipment, and trainers with conflict detection (Resource Booking). |
| **SR-05** | **Dynamic Waitlist:** Automatic first-in-first-out (FIFO) waitlist logic. If a seat opens up, the next person in line is promoted. |

### 1.3 Functional Requirements (FR)
| ID | Requirement Description |
|:---|:---|
| **FR-01** | Learners must submit evaluation forms after each session. |
| **FR-02** | Learners can cancel registrations after approval due to business conflicts. |
| **FR-03** | L&D Officers can design custom feedback forms (Likert-scale, Open questions). |
| **FR-04** | Automated QR code generation for evaluation forms. |
| **FR-05** | Automated reminders (N days before session) based on Officer configuration. |
| **FR-06** | Workflow: Draft -> Line Manager Approval -> Planned. |
| **FR-07** | L&D Officers can directly assign mandatory sessions to learners. |
| **FR-08** | Support for 3 Course Types: Public Sessions, Request Sessions, and Assigned Sessions. |
| **FR-10** | Document attachment support for course materials (Pre/Post-session). |
| **FR-11** | Attendance tracking (Attended / Absent / Late). |
| **FR-12** | **Completion Definition:** Attendance + (Optional) Test + (Mandatory) Feedback Form. |
| **FR-13** | **Pass/Fail Logic:** Completion is binary based on (Attendance = Yes) AND (Score >= Threshold). |
| **FR-14** | **Automated Certificates:** Trigger PDF generation and email delivery upon reaching "Pass" state. |
| **FR-15** | **Skill Auto-Update:** Automatic injection of skills into `hr.employee` profile upon passing. |

---

## 2. Section 2: Proactive Expert Recommendations (System Enhancements)

### 2.1 Analytics & Efficacy (The Kirkpatrick Model)
| ID | Requirement Description |
|:---|:---|
| **ER-01** | **Level 3 Behavior Assessment:** Implement a "Post-Training Impact Survey" sent to Line Managers 90 days after course completion to measure skill application. |
| **ER-02** | **Skill Level Graduation:** Instead of just adding a skill, implement logic to increment current skill levels (e.g., Level 1 -> Level 2) based on course difficulty. |
| **ER-03** | **ROI Calculation:** Automated reporting comparing training costs against performance appraisal trends (Productivity vs. Training Hours). |

### 2.2 Operational Efficiency
| ID | Requirement Description |
|:---|:---|
| **ER-04** | **E-Learning Integration (SCORM/xAPI):** Framework support for hosting digital content to allow asynchronous learning alongside physical sessions. |
| **ER-05** | **Budget Quotas:** Allow L&D Managers to set department-specific annual training budgets with "Soft/Hard" limit warnings during approval. |
| **ER-06** | **Prerequisite Management:** Dependency logic where Course B cannot be requested until Course A is passed. |

### 2.3 User Experience (UX)
| ID | Requirement Description |
|:---|:---|
| **ER-07** | **Gamification (Badges):** Integration with Odoo's `gamification` module to award digital badges upon certification. |
| **ER-08** | **Calendar Integration:** Automatic sync of "Planned Sessions" with Learner's Odoo/Outlook/Google Calendar. |
| **ER-09** | **Mobile Quick-Check-in:** QR code scanning by L&D Officers for rapid attendance marking via tablet or phone. |
