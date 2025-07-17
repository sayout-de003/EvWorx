EvWorx

EvWorx is a robust web application built using Django, designed to serve as a marketplace for electric vehicle (EV) parts. The platform allows users to browse, search, and purchase premium EV parts. It includes user authentication, product management, shopping cart, orders, and an admin interface. The project emphasizes clean architecture, modularity, and scalability.

Key Features

Product Catalog: Browse parts with search, filtering, and categorization.
Authentication System: User registration, login, logout, and session management.
Shopping Cart: Add, update, or remove items before checkout.
Order Management: Checkout flow with order summary and confirmation.
Wishlist Support: Save products for later.
Admin Dashboard: Full CRUD operations for products and users.
Coupon System (optional): Apply promotional discounts at checkout.
Media and Static File Handling: Support for images and stylesheets.
Secure Environment Configuration using .env.
Technologies Used

Backend: Django, Django REST Framework
Frontend: HTML, Tailwind CSS
Database: SQLite (easily replaceable with PostgreSQL or MySQL)
Other: Pillow, dotenv, Cloudflare Tunnel
Setup Instructions

1. Clone the Repository
git clone https://github.com/sayout-de003/EvWorx.git
cd EvWorx
2. Create and Activate Virtual Environment
python -m venv evw
source evw/bin/activate  # macOS/Linux
# For Windows: evw\Scripts\activate
3. Install Required Packages
pip install -r requirements.txt
4. Configure Environment Variables
Create a .env file in the project root and define the following variables:

SECRET_KEY=your-django-secret-key
DEBUG=True
Note: .env is already excluded from version control via .gitignore.
5. Apply Migrations
python manage.py migrate
6. Create Superuser (for Admin Panel Access)
python manage.py createsuperuser
7. Run the Development Server
python manage.py runserver
8. Optional: Expose Localhost via Cloudflare Tunnel
cloudflared tunnel --url http://localhost:8000
Directory Structure

        evault/
        ├── core/
        │   ├── __init__.py
        │   ├── admin.py
        │   ├── apps.py
        │   ├── models.py
        │   ├── serializers.py
        │   ├── tests.py
        │   ├── urls.py
        │   ├── views.py
        │   ├── migrations/
        │   ├── management/
        │   │   └── commands/
        │   └── templates/
        │       └── core/
        │           ├── about.html
        │           ├── base.html
        │           ├── blog.html
        │           ├── blog_detail.html
        │           ├── cart.html
        │           ├── catalog.html
        │           ├── faq.html
        │           ├── garage.html
        │           ├── homepage.html
        │           ├── login.html
        │           ├── order_create.html
        │           ├── signup.html
        │           └── wishlist.html
        ├── evault/
        │   ├── __init__.py
        │   ├── asgi.py
        │   ├── settings.py
        │   ├── urls.py
        │   └── wsgi.py
        ├── media/
        ├── manage.py
        ├── README.md
        └── requirements.txt




Deployment Notes

The project uses PostgreSQL for local development.
You can configure a production database (PostgreSQL or MySQL) via environment variables in .env.
For static files in production, consider using whitenoise or AWS S3.
License

This project is currently private and intended for educational and development use only. Licensing terms will be updated in future iterations.

