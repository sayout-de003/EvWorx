from locust import HttpUser, task, between
import random

# Sample product slugs for testing
PRODUCT_SLUGS = [
    "product-1", "product-2", "product-3", "product-4",
    "product-5", "product-6", "product-7", "product-8"
]

class WebsiteUser(HttpUser):
    wait_time = between(1, 3)  # wait between requests to simulate real user

    @task(5)
    def view_homepage(self):
        self.client.get("/")

    @task(2)
    def view_about(self):
        self.client.get("/about/")

    @task(2)
    def view_faq(self):
        self.client.get("/faq/")

    @task(5)
    def view_catalog(self):
        # Randomize page number and sort
        page = random.randint(1, 3)
        sort = random.choice(["name_asc", "name_desc", "price_asc", "price_desc"])
        self.client.get(f"/catalog/?page={page}&sort={sort}")

    @task(4)
    def view_product(self):
        slug = random.choice(PRODUCT_SLUGS)
        self.client.get(f"/product/{slug}/")

    @task(3)
    def signup(self):
        self.client.post("/signup/", {
            "username": f"user{random.randint(1000,9999)}",
            "email": f"user{random.randint(1000,9999)}@test.com",
            "password1": "Password123",
            "password2": "Password123"
        })

    @task(3)
    def login(self):
        self.client.post("/login/", {
            "username": "testuser",
            "password": "testpassword"
        })

    @task(4)
    def cart_and_wishlist(self):
        self.client.get("/cart/")
        self.client.get("/wishlist/")

    @task(2)
    def create_order(self):
        self.client.get("/order/")
        self.client.post("/order/", {
            # If your order_create view expects POST data, add here
        })
        self.client.get("/order/confirm/")
        self.client.get("/order/payment/")
