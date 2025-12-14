# Ebook Cart Web App - Technical Requirements

## Product
**Parallel Critiques: Analyzing Rhetorical Extremism**  
Single product, 4 licensing tiers, secure digital delivery

---

## Core Features

### 1. Product Page
- Book title, subtitle, cover image
- Description and key findings
- Back cover text
- Sample chapter download (lead generation)
- Pricing tier selector/comparison table
- Add to cart button for each tier

### 2. Shopping Cart
- Single product focus
- Shows selected license tier
- Clear pricing display
- Quantity selector (for Corporate bulk purchases)
- Apply discount code field
- Secure checkout button

### 3. Checkout
- Email collection (required)
- Payment processing (Square integration)
- License type confirmation
- Billing information
  - Individual: Name, email, card
  - Corporate: Company name, billing address, optional PO number
- Terms acceptance checkbox
- Secure payment (PCI compliant via Square)

### 4. Post-Purchase
- Immediate confirmation page
- Email with:
  - Receipt/invoice
  - Download link(s)
  - License key
  - License terms document
  - Access to customer portal
- Redirect to download portal

### 5. Download Portal
- Secure login (email + license key)
- Download files:
  - PDF (watermarked with license holder info)
  - EPUB
  - MOBI
  - Jupyter notebooks (ZIP)
  - Datasets (CSV, ZIP)
  - Visualizations (high-res PNG)
- License information display
- Download tracking
- Re-download capability

### 6. License Management (For Corporate/Enterprise)
- Admin dashboard for license holder
- Add/remove team members
- View download activity
- Manage seat allocations
- Download usage reports

---

## Licensing Tiers

### Individual - $14.99
- Single user
- Immediate download
- Personal use only

### Academic/Educational - $99.99
- Up to 50 students
- Classroom distribution rights
- Instructor materials
- Annual license

### Corporate/Agency - $499.99
- Up to 100 employees
- Multi-user portal access
- Internal training rights
- Priority support
- Annual license

### Enterprise/Government - Custom
- Unlimited employees
- Custom negotiation
- Contact sales form
- Manual processing

---

## Technical Stack

### Frontend
- **Framework**: React or Next.js
- **Styling**: Tailwind CSS
- **Responsive**: Mobile-first design
- **Forms**: React Hook Form + validation

### Backend
- **Framework**: Flask (Python) or Node.js/Express
- **Database**: PostgreSQL
  - Users/customers
  - Orders
  - Licenses
  - Downloads (tracking)
- **File Storage**: Local file system on web server
- **Authentication**: JWT tokens for download portal

### Payment Processing
- **Square Checkout** for payment processing
- Webhook handling for payment confirmation
- Invoice generation
- Refund capability

### Email Service
- **SendGrid** or **AWS SES**
- Transactional emails:
  - Order confirmation
  - Download links
  - License keys
  - Password resets
  - Annual renewal reminders

### Security
- SSL/TLS (HTTPS everywhere)
- PCI compliance (via Square)
- Password hashing (bcrypt)
- Rate limiting
- CSRF protection
- License key generation (secure random)
- File watermarking (PDF)
- Download link expiration (24-hour tokens)

### Hosting
- **Backend**: Heroku, AWS, or DigitalOcean
- **Frontend**: Vercel or Netlify
- **Database**: Managed PostgreSQL (AWS RDS or Heroku)
- **File Storage**: Local storage on backend server

---

## Database Schema

### customers
```sql
- id (PK)
- email (unique)
- name
- company_name (nullable)
- created_at
- updated_at
```

### orders
```sql
- id (PK)
- customer_id (FK)
- license_tier (enum: individual, academic, corporate, enterprise)
- amount_paid
- stripe_payment_id
- purchase_order_number (nullable)
- status (enum: pending, completed, refunded)
- created_at
```

### licenses
```sql
- id (PK)
- order_id (FK)
- license_key (unique)
- license_tier
- seats_total (for multi-user licenses)
- seats_used
- expiration_date (nullable, for annual licenses)
- is_active
- created_at
```

### license_users (for multi-user licenses)
```sql
- id (PK)
- license_id (FK)
- email
- added_at
- last_download_at
```

### downloads
```sql
- id (PK)
- license_id (FK)
- user_email
- file_name
- downloaded_at
- ip_address
```

---

## User Flows

### Individual Purchase Flow
1. Land on product page
2. Click "Buy Individual License - $14.99"
3. Checkout (email, payment)
4. Payment processed
5. Confirmation page with download links
6. Email with license key and access
7. Download files immediately

### Corporate Purchase Flow
1. Land on product page
2. Select "Corporate License - $499.99"
3. Checkout (company info, payment or PO)
4. Payment processed (or pending for PO)
5. Admin receives license key
6. Admin logs into portal
7. Admin adds employee emails
8. Employees receive download invitations
9. Employees download files

### Enterprise Contact Flow
1. Click "Contact for Enterprise Pricing"
2. Fill out contact form (name, company, needs)
3. Form submitted
4. Sales notification sent
5. Manual follow-up and negotiation
6. Custom license created

---

## MVP Features (Launch v1.0)

### Must Have
✓ Product page with tier comparison  
✓ Square checkout integration  
✓ Automated email delivery  
✓ Secure download portal (email + license key login)  
✓ PDF watermarking with license holder info  
✓ Basic admin panel (view orders, licenses)  
✓ Mobile responsive design  

### Can Wait (v1.1+)
- Multi-user portal for Corporate tier
- Seat management dashboard
- Download analytics
- Renewal automation
- Discount codes
- Volume discount calculator
- Integration with institutional SSO

---

## Pages/Routes

### Public Pages
- `/` - Product landing page
- `/sample` - Free sample chapter download
- `/pricing` - Detailed pricing comparison
- `/terms` - Terms of service
- `/privacy` - Privacy policy
- `/contact` - Enterprise contact form

### Checkout Flow
- `/checkout` - Square checkout integration
- `/confirmation` - Post-purchase confirmation
- `/download` - Secure download portal

### Admin
- `/admin` - Admin dashboard (orders, licenses, analytics)
- `/admin/customers` - Customer management
- `/admin/licenses` - License management

---

## File Deliverables (What Gets Downloaded)

### All Tiers Include:
1. **ebook_parallel_critiques.pdf** (watermarked)
2. **ebook_parallel_critiques.epub**
3. **ebook_parallel_critiques.mobi**
4. **methodology_appendix.pdf**
5. **visualizations.zip** (all PNG charts)
6. **datasets.zip** (CSV files)
7. **jupyter_notebooks.zip** (interactive analysis)
8. **license_terms.pdf**

### Academic Tier Adds:
9. **instructor_guide.pdf**
10. **discussion_questions.pdf**
11. **assignment_templates.zip**

### Corporate Tier Adds:
12. **executive_summary.pdf**
13. **presentation_deck.pptx**
14. **training_materials.zip**

---

## Development Phases

### Phase 1: MVP (2-3 weeks)
- Product page
- Square integration (Individual tier only)
- Email delivery
- Basic download portal
- Deploy to production

### Phase 2: Multi-Tier (1-2 weeks)
- Add Academic/Corporate tiers
- License key system
- Watermarking
- Admin panel

### Phase 3: Corporate Features (2-3 weeks)
- Multi-user portal
- Seat management
- Corporate billing (PO, invoices)
- Analytics dashboard

### Phase 4: Enterprise & Polish (1-2 weeks)
- Contact form for Enterprise
- Renewal reminders
- Enhanced security
- Performance optimization

---

## Budget Estimate (Monthly Operational Costs)

- **Hosting**: $20-50/month (Heroku/DigitalOcean)
- **Database**: $20-30/month (managed PostgreSQL)
- **Email Service**: $10/month (SendGrid - up to 40k emails)
- **Square Fees**: 2.9% + $0.30 per transaction
- **SSL Certificate**: Free (Let's Encrypt)
- **Domain**: $12/year

**Total**: ~$50-100/month + transaction fees

---

## Success Metrics to Track

- Conversion rate (visitors → purchases)
- Average order value
- Tier distribution (% Individual vs Corporate)
- Download completion rate
- Customer support tickets
- Refund rate
- Corporate renewal rate

---

## Next Steps

1. Finalize tech stack decision (Flask vs Node.js)
2. Set up development environment
3. Design mockups for key pages
4. Set up Square account and test mode
5. Build MVP (Individual tier only)
6. Test payment and delivery flow
7. Deploy beta version
8. Add remaining tiers
9. Launch publicly
