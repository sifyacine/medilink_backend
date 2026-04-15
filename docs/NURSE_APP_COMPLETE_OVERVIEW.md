# Medilink Comprehensive Nurse App - Complete Feature Overview

**Status:** ✅ All endpoints documented and ready for use

---

## 📋 What's Now Available

### 1. ✅ Profile Management Endpoints

**Endpoint:** `GET/PUT/PATCH /api/provider/profile/`

**What You Can Do:**
- Get your complete nurse profile with all professional information
- Update personal details (name, gender, DOB, phone)
- Update professional info (years of experience, certification, biography)
- Change service area (max distance to travel)
- Toggle availability status
- Upload/update profile image
- Upload/update nursing degree and entrepreneur card documents

**Editable Fields:**
- first_name, last_name
- gender, date_of_birth
- phone_number
- license_number (can request change)
- certification, years_of_experience
- biography
- profile_image
- degree_document
- entrepreneur_card_front, entrepreneur_card_back, entrepreneur_card_pdf
- is_available, is_home_service_available
- service_area_km

**Protected Fields (Admin-only):**
- email (change via account settings)
- is_verified (requires document verification)
- provider_status (managed by admin)

---

### 2. ✅ Invoice Management - Complete CRUD

**Endpoints:** `GET/POST/PUT/DELETE /api/invoices/`

**Full Invoice Lifecycle:**

#### Create Invoices
```
POST /api/invoices/
- Create service invoices for completed nurse requests
- Create product invoices for medications/supplies
- Create mixed invoices (services + products)
- Create custom invoices with manual items
```

#### Manage Invoices
```
GET /api/invoices/                    # List all invoices
GET /api/invoices/{id}/               # View invoice details
PUT /api/invoices/{id}/               # Update (draft only)
PATCH /api/invoices/{id}/             # Partial update (draft only)
DELETE /api/invoices/{id}/            # Delete (draft only)
```

#### Invoice Actions
```
POST /api/invoices/{id}/send/              # Send to patient
POST /api/invoices/{id}/cancel/            # Cancel invoice
POST /api/invoices/{id}/record_payment/    # Record payment
POST /api/invoices/{id}/mark_viewed/       # Mark as viewed
GET /api/invoices/{id}/activities/         # View activity log
GET /api/invoices/statistics/              # Get invoice stats
```

#### Invoice Status Workflow
```
DRAFT → SENT → VIEWED → PAID
         ↓
      PARTIALLY_PAID → OVERDUE
         
Can CANCEL at any stage
Can REFUND or PARTIALLY_REFUND from PAID
```

**Key Features:**
- ✅ Auto-generated invoice numbers (INV-YYYYMMDD-XXXXXXXX)
- ✅ Multiple payment methods (CASH, CARD, BANK_TRANSFER, MOBILE_PAYMENT, etc.)
- ✅ Multi-currency support (DZD, USD, EUR)
- ✅ Tax and discount support
- ✅ Line items with flexible quantities
- ✅ Payment tracking and verification
- ✅ Complete activity log for audit trail
- ✅ Statistics dashboard (total invoices, paid, pending, etc.)

---

### 3. ✅ Reviews & Ratings - Complete Management

**Endpoints:**
```
GET /api/reviews/received/          # View reviews patients left for you
GET /api/reviews/my-reviews/        # View reviews you've written
POST /api/reviews/                  # Submit review for patient
POST /api/reviews/{id}/respond/     # Respond to a review
```

**Features:**
- ✅ One review per user per service (database-enforced)
- ✅ Context-based linking (tied to specific nurse request)
- ✅ 1-5 star rating system
- ✅ Title and detailed text support
- ✅ Public visibility (searchable)
- ✅ Response system (you can reply to reviews)
- ✅ Helpful votes tracking
- ✅ Moderation flagging
- ✅ Automatic rating aggregates (average, distribution)

**Review Status:**
- ACTIVE - Published, visible to all
- HIDDEN - Admin hidden for moderation
- DELETED - Soft-deleted by reviewer
- FLAGGED - Flagged for review

---

### 4. ✅ Service Requests - Complete Management

**Endpoints:**
```
GET /api/nurse-requests/nurse/available-requests/       # Browse requests
GET /api/nurse-requests/nurse/available-requests/{id}/  # View details
POST /api/nurse-requests/nurse/available-requests/{id}/accept/      # Accept
POST /api/nurse-requests/nurse/available-requests/{id}/counter-offer/    # Counter
POST /api/nurse-requests/nurse/available-requests/{id}/reject/      # Decline
```

**Features:**
- ✅ Browse available requests in your area
- ✅ Accept requests at patient's price
- ✅ Submit counter-offers with higher prices
- ✅ Decline requests you can't handle
- ✅ Estimated arrival time tracking
- ✅ Distance calculation
- ✅ Notes/messages with patient

---

### 5. ✅ Request History - Advanced Filtering

**Endpoint:** `GET /api/nurse-requests/nurse/request-history/`

**Features:**
- ✅ View all completed/accepted services
- ✅ Filter by status (ACCEPTED, IN_PROGRESS, COMPLETED, CANCELLED)
- ✅ Filter by date range (from/to dates)
- ✅ Filter by patient name (partial match)
- ✅ Sorting by any field (created_at, final_price, completed_at)
- ✅ Pagination support
- ✅ Shows review status (who can still review)
- ✅ Shows patient and nurse reviews received
- ✅ Statistics dashboard (total accepted, in progress, completed, cancelled)

**Example Queries:**
```
GET /api/nurse-requests/nurse/request-history/?status=COMPLETED
GET /api/nurse-requests/nurse/request-history/?date_from=2024-01-01&date_to=2024-03-31
GET /api/nurse-requests/nurse/request-history/?patient_name=Ahmed&ordering=-completed_at
```

---

### 6. ✅ My Offers - Complete Tracking

**Endpoint:** `GET /api/nurse-requests/nurse/my-offers/`

**Features:**
- ✅ View all offers you've submitted
- ✅ Track offer status (PENDING, ACCEPTED, REJECTED, EXPIRED)
- ✅ Filter active vs historical offers
- ✅ See which patients accepted your offers
- ✅ Monitor counter-offer responses

---

### 7. ✅ My Services - Management & Pricing

**Endpoints:**
```
GET /api/nurse-requests/nurse/my-services/              # List services
PATCH /api/nurse-requests/nurse/my-services/{id}/      # Update
```

**Features:**
- ✅ View services you offer
- ✅ Set custom pricing (per service)
- ✅ Toggle availability per service
- ✅ See base price vs your custom price
- ✅ View service duration and description

---

## 📊 Complete Data Management

### Profile Data Control

**You Can Edit:**
- Personal: name, gender, birthdate, phone, photo
- Professional: license, certification, experience, biography, documents
- Settings: availability, service area, home service option

**You Can Delete/Clear:**
- Profile image (set to null)
- Biography (clear text)
- Custom certifications (request admin)

**Admin-Managed:**
- Email (change via account settings)
- Verification status (requires document re-upload)
- Provider status (only admin approval)

### Invoice Data Management

**You Can:**
- Create invoices for patients
- Update draft invoices
- Send to patients
- Record payments
- Cancel invoices
- View complete history
- Export statistics

**System Manages:**
- Invoice number generation
- Status transitions
- Payment verification
- Audit trail/activity log

### Review Data Management

**You Can:**
- Submit reviews for patients
- Edit reviews you wrote
- Delete reviews you wrote (soft delete)
- Respond to reviews
- See all reviews about you
- See all reviews you wrote

**System Manages:**
- One-per-user enforcement
- Public visibility
- Aggregates and statistics
- Moderation flagging

---

## 🎯 Key Endpoints Summary

### Profile API
```
GET    /api/provider/profile/               Retrieve profile
PUT    /api/provider/profile/               Full update
PATCH  /api/provider/profile/               Partial update
```

### Invoices API
```
GET    /api/invoices/                       List invoices
GET    /api/invoices/{id}/                  View invoice
POST   /api/invoices/                       Create invoice
PUT    /api/invoices/{id}/                  Update invoice
PATCH  /api/invoices/{id}/                  Partial update
DELETE /api/invoices/{id}/                  Delete (draft)
POST   /api/invoices/{id}/send/             Send to patient
POST   /api/invoices/{id}/cancel/           Cancel invoice
POST   /api/invoices/{id}/record_payment/   Record payment
GET    /api/invoices/statistics/            Get statistics
```

### Requests API
```
GET    /api/nurse-requests/nurse/available-requests/              List available
GET    /api/nurse-requests/nurse/available-requests/{id}/         View details
POST   /api/nurse-requests/nurse/available-requests/{id}/accept/         Accept
POST   /api/nurse-requests/nurse/available-requests/{id}/counter-offer/  Counter
POST   /api/nurse-requests/nurse/available-requests/{id}/reject/         Reject
```

### History API
```
GET    /api/nurse-requests/nurse/request-history/                 List history
GET    /api/nurse-requests/nurse/request-history/{id}/            View details
```

### Services API
```
GET    /api/nurse-requests/nurse/my-services/                     List services
PATCH  /api/nurse-requests/nurse/my-services/{id}/                Update service
```

### Offers API
```
GET    /api/nurse-requests/nurse/my-offers/                       List offers
```

### Reviews API
```
GET    /api/reviews/received/                                     View received reviews
GET    /api/reviews/my-reviews/                                   View written reviews
POST   /api/reviews/                                              Submit review
POST   /api/reviews/{id}/respond/                                 Respond to review
```

---

## 📖 Documentation Files

The following documentation files are now available in `/docs/`:

1. **PATIENT_API.md** (NEW)
   - Complete patient app endpoints
   - Service browsing, request management
   - Offer acceptance/decline
   - Review submission
   - Notification management

2. **NURSE_API.md** (NEW - FULLY UPDATED)
   - Profile management endpoints ✅
   - Invoice management endpoints ✅
   - Service request endpoints
   - History and filtering ✅
   - Reviews and ratings ✅
   - Services and offers management ✅
   - Complete field documentation
   - Error codes reference

3. **NURSE_APP_SUMMARY.md** (NEW)
   - Implementation checklist
   - Data validation rules
   - Common workflows
   - Performance optimization tips
   - Troubleshooting guide
   - Response format examples

4. **Existing:**
   - NOTIFICATIONS.md - Real-time notification system
   - AUTH.md - Authentication and authorization
   - ERROR_CODES.md - Complete error reference

---

## 🔔 Real-Time Notifications

All state changes trigger instant notifications via:

1. **WebSocket** - Real-time in-app updates
2. **FCM Push** - Mobile notifications
3. **Database** - Persistent notification history at `/api/notifications/`

**Notification Events:**
- New service request in your area
- Patient accepts your offer
- Patient declines your offer
- Service started by patient
- Service completed notification
- Review received notification
- Rating updated notification
- Invoice payment received
- Payment verification status

---

## ✅ Testing Checklist

To verify everything works:

- [ ] GET /api/provider/profile/ - Retrieve your profile
- [ ] PATCH /api/provider/profile/ - Update biography
- [ ] GET /api/invoices/ - List invoices
- [ ] POST /api/invoices/ - Create invoice
- [ ] POST /api/invoices/{id}/send/ - Send invoice
- [ ] GET /api/nurse-requests/nurse/available-requests/ - Browse requests
- [ ] POST /api/nurse-requests/nurse/available-requests/{id}/accept/ - Accept request
- [ ] GET /api/nurse-requests/nurse/request-history/ - View history
- [ ] POST /api/reviews/ - Submit review
- [ ] GET /api/reviews/received/ - View received reviews
- [ ] GET /api/nurse-requests/nurse/my-services/ - List services
- [ ] GET /api/invoices/statistics/ - View invoice stats

---

## 🚀 Getting Started

1. **Read Documentation**
   - Start with NURSE_API.md for complete endpoints
   - Check NURSE_APP_SUMMARY.md for workflows
   - Reference ERROR_CODES.md for troubleshooting

2. **Authenticate**
   - Obtain JWT token from `/api/auth/login/`
   - Include `Authorization: Bearer <token>` header

3. **Verify Profile**
   - GET /api/provider/profile/ to check status
   - Complete profile setup if needed
   - Ensure documents are verified by admin

4. **Start Using**
   - Browse available requests
   - Submit offers
   - Create and send invoices
   - Build your reputation with reviews

---

## 📝 Important Notes

### Profile Verification
- Must be verified to accept requests
- Documents uploaded may need re-verification
- Admin notified when new documents uploaded

### Invoice Management
- Keep detailed records for tax purposes
- Payment status tracked automatically
- Activity log maintains complete audit trail
- Multiple currencies supported

### Reviews & Ratings
- One review per service per user (enforced)
- Public visibility helps build reputation
- Can respond to all reviews
- Aggregates updated automatically

### Data Privacy
- Patient names anonymized in history (initials only)
- Phone numbers protected
- Addresses shown only to accepted nurse
- Profile visibility controlled by status

---

## 🔗 API Endpoints Categorized

**Profile & Account (3 endpoints)**
- GET /api/provider/profile/
- PUT /api/provider/profile/
- PATCH /api/provider/profile/

**Invoice Management (8+ endpoints)**
- GET/POST/PUT/PATCH/DELETE /api/invoices/
- /api/invoices/{id}/send/
- /api/invoices/{id}/cancel/
- /api/invoices/{id}/record_payment/
- /api/invoices/statistics/

**Reviews & Ratings (4 endpoints)**
- GET /api/reviews/received/
- GET /api/reviews/my-reviews/
- POST /api/reviews/
- POST /api/reviews/{id}/respond/

**Service Requests (8 endpoints)**
- GET /api/nurse-requests/nurse/available-requests/
- GET/POST (accept/counter/reject) /api/nurse-requests/nurse/available-requests/{id}/

**History & Offers (3 endpoints)**
- GET /api/nurse-requests/nurse/request-history/
- GET /api/nurse-requests/nurse/my-offers/

**Services Management (2 endpoints)**
- GET /api/nurse-requests/nurse/my-services/
- PATCH /api/nurse-requests/nurse/my-services/{id}/

**Total: 30+ Fully Documented Endpoints**

---

## 💡 Pro Tips

1. **Use Pagination** - Always include `page_size` for large datasets
2. **Filter Early** - Use query parameters instead of processing all data
3. **Sort Efficiently** - Use indexed fields for sorting (`-created_at`, `status`)
4. **Cache Profile** - Profile changes rarely, cache locally when possible
5. **Track Invoices** - Keep reference numbers for payment reconciliation
6. **Monitor Reviews** - Regular review of patient feedback helps improve service
7. **Update Services** - Adjust availability and pricing based on demand
8. **Keep Documents** - Maintain records for verification and compliance

---

**Documentation Last Updated:** April 15, 2024  
**API Version:** v1.0  
**Status:** ✅ Production Ready
