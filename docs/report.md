# UniSwap: Campus-Only Peer-to-Peer Marketplace System
**Course Engineering Report & System Specification**

---

## 1. Executive Summary
College students routinely spend hundreds of dollars each semester on single-use academic items such as STEM textbooks, graphing calculators, organic chemistry lab coats, and specialty electronics. Existing generic classifieds (Craigslist, Facebook Marketplace) fail to provide campus-level trust, require sharing personal contact information with strangers, and expose students to non-academic fraud.

**UniSwap** solves this problem by creating an institutional-walled marketplace exclusively for college students. By gating access through verified college email domains (e.g., `@state.edu`), transactions take place in safe physical campus environments between recognized academic peers. The system is built with Django 5.x following clean architectural standards: cryptographic verification tokens, transactional state machines, strict ownership verification, live SQL aggregation for seller trust, and total elimination of Insecure Direct Object Reference (IDOR) vulnerabilities.

---

## 2. Problem Statement & Campus Requirements
1. **Strict Institutional Gating:** No unverified accounts or outside actors may inspect student listings, contact sellers, or view student profiles.
2. **Accurate Academic Categorization:** Tailored taxonomies for Textbooks, Calculators, Lab Coats, Electronics, and Other with clear condition tiers (New, Like New, Good, Fair).
3. **Structured Hand-off Workflow:** Avoid informal ghosting through a formal transaction state machine that reserves inventory and records completion upon in-person exchange.
4. **Tamper-Proof Reputation:** Verified ratings accessible only after transaction completion, calculated directly with database aggregation to prevent score manipulation.

---

## 3. High-Level Architecture & Stack
- **Backend:** Python 3.12+, Django 5.x
- **Database:** SQLite (development), PostgreSQL via `dj-database-url` (production)
- **Image Handling:** Pillow (Django ImageField)
- **Frontend:** Server-rendered Django templates with pure CSS (no build step, zero JS runtime overhead)
- **Testing:** Django's native test runner (32 unit/integration tests)

### Modular App Layout
- `accounts`: Custom `User` (AbstractUser), `Campus` model, signed email verification, and public profiles.
- `listings`: `Category`, `Listing`, `ListingImage`, multi-criteria filtering and search.
- `messaging`: Scoped `Conversation` and `Message` models with unique buyer-listing chats.
- `transactions`: `Transaction` finite state machine (`Requested -> Agreed -> Completed -> Cancelled`).
- `reviews`: `Review` model with `OneToOneField` to `Transaction` and live `Avg` rating aggregation.

---

## 4. Security & Access Control Architecture
### 4.1 Domain Verification Gate
The allowed email domain is stored in the `Campus` model rather than hard-coded in settings. During signup:
1. The domain is parsed from the student's email.
2. An active campus must match the domain, or registration fails.
3. Django's `TimestampSigner` generates a cryptographically signed token valid for 3 days.
4. Unverified students are blocked from all marketplace views via `VerifiedRequiredMixin`.

### 4.2 Zero-IDOR Enforcement
Every endpoint accepting an identifier filters querysets by the authenticated user before executing `get_object_or_404`. For example:
```python
user_conversations = Conversation.objects.filter(
    Q(buyer=request.user) | Q(seller=request.user)
)
conversation = get_object_or_404(user_conversations, pk=conv_id)
```
Non-participants receive an HTTP 404 Not Found error, preventing enumeration or tampering.

---

## 5. Transaction State Machine
The purchase workflow is governed by strict deterministic rules:
- **Requested:** Buyer initiates request on an active listing.
- **Agreed:** Only the seller can agree. Listing status transitions to `Reserved`.
- **Completed:** Either buyer or seller confirms completion upon meetup. Listing status transitions to `Sold`, and `completed_at` timestamp is recorded.

Invalid transitions raise an explicit HTTP 400 Bad Request error rather than failing silently.

---

## 6. Seller Rating Integrity
- Reviews are only allowed on `Completed` transactions.
- A `CheckConstraint` enforces `reviewer != reviewee`.
- Only transaction participants can submit a review, and only once per deal.
- Seller rating is calculated on-demand using `Review.objects.filter(reviewee=user).aggregate(Avg('rating'))['rating__avg']`, eliminating denormalization anomalies.

---

## 7. Testing & Verification Summary
UniSwap includes 32 automated tests covering:
- Verification gate blocking unverified access to listings, details, creation, messaging, and profiles.
- Ownership checks preventing non-owners from editing or deleting listings.
- Status update to `Removed` rather than table deletion.
- IDOR 404 responses for non-participants across conversations, transactions, and reviews.
- Transaction state machine transition validation.
- Review gating and rating aggregation accuracy.
- Email domain validation during signup.

---

## 8. Out-of-Scope Architecture Rationale
- **Payment Gateways:** Campus goods trades are cash/P2P physical exchanges; removing digital processing eliminates chargebacks and fees.
- **WebSockets:** Standard HTTP polling/reloads are simple, robust, and require minimal hosting overhead.
- **Administrative Moderation:** Closed campus email domains and verified peer reviews provide community self-regulation.

