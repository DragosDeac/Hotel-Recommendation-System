from locust import HttpUser, TaskSet, task, between
from bs4 import BeautifulSoup
import logging

# Log in conf
logging.basicConfig(level=logging.INFO)

class UserBehavior(TaskSet):

    def get_csrf_token(self, url):
        """Extrage token-ul CSRF de pe pagina specificată"""
        response = self.client.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            csrftoken = soup.find('input', dict(name='csrfmiddlewaretoken'))['value']
            return csrftoken
        else:
            logging.error(f"Failed to load page {url}: {response.status_code} - {response.text}")
            return None

    def on_start(self):
        """Logare automată la începutul sesiunii Locust"""
        self.login()

    def login(self):
        """Task pentru simularea login-ului și redirecționare în funcție de rol"""
        logging.info("Attempting login")
        csrftoken = self.get_csrf_token("/login/")

        if csrftoken:
            response = self.client.post("/login/", {
                "username": "testuser",
                "password": "password123",
                "csrfmiddlewaretoken": csrftoken
            }, headers={'X-CSRFToken': csrftoken})

            if response.status_code == 200:
                logging.info("Login successful")
                if 'renter' in response.text:
                    self.user_role = 'renter'
                    logging.info("Logged in as Renter")
                elif 'landlord' in response.text:
                    self.user_role = 'landlord'
                    logging.info("Logged in as Landlord")
            else:
                logging.error(f"Login failed: {response.status_code} - {response.text}")
        else:
            logging.error("Failed to retrieve CSRF token for login")

    @task
    def profile_actions(self):
        """Simulează acțiuni pentru Renter sau Landlord după login"""
        if hasattr(self, 'user_role'):
            if self.user_role == 'renter':
                self.renter_actions()
            elif self.user_role == 'landlord':
                self.landlord_actions()

    def renter_actions(self):
        """Task-uri specifice utilizatorilor Renter"""
        self.view_profile()
        self.view_acasa()
        self.submit_review()

    def landlord_actions(self):
        """Task-uri specifice utilizatorilor Landlord"""
        self.view_landlord()
        self.edit_hotel()
        self.new_hotel()

    @task
    def view_profile(self):
        """Task pentru vizualizarea profilului Renter"""
        logging.info("Attempting to view renter profile")
        response = self.client.get("/profile/")
        if response.status_code == 200:
            logging.info("Profile view successful")
        else:
            logging.error(f"Failed to view profile: {response.status_code} - {response.text}")

    @task
    def view_acasa(self):
        """Task pentru vizualizarea paginii principale (acasa) pentru Renter"""
        logging.info("Attempting to view 'acasa' page")
        response = self.client.get("/acasa/")
        if response.status_code == 200:
            logging.info("Acasa page view successful")
        else:
            logging.error(f"Failed to view 'acasa' page: {response.status_code} - {response.text}")

    @task
    def submit_review(self):
        """Task pentru trimiterea unei recenzii la un sejur anterior"""
        logging.info("Attempting to submit a review")

        # Sejours 
        stays_response = self.client.get("/profile/")  # Endpoint for hotels
        if stays_response.status_code == 200:
            stays = stays_response.json()  
            if stays:
                stay_id = stays[0]['id']  # First stay
                csrftoken = self.get_csrf_token(f"/submit_review/{stay_id}/")
                if csrftoken:
                    response = self.client.post(f"/submit_review/{stay_id}/", {
                        "rating": 5,
                        "csrfmiddlewaretoken": csrftoken
                    }, headers={'X-CSRFToken': csrftoken})

                    if response.status_code == 200:
                        logging.info("Review submitted successfully")
                    else:
                        logging.error(f"Failed to submit review: {response.status_code} - {response.text}")
                else:
                    logging.error("Failed to retrieve CSRF token for review submission")
            else:
                logging.error("No stays available for review")
        else:
            logging.error(f"Failed to retrieve stays: {stays_response.status_code} - {stays_response.text}")


    @task
    def view_landlord(self):
        """Task pentru vizualizarea paginii landlord"""
        logging.info("Attempting to view landlord page")
        response = self.client.get("/landlord/")
        if response.status_code == 200:
            logging.info("Landlord page view successful")
        else:
            logging.error(f"Failed to view landlord page: {response.status_code} - {response.text}")

    @task
    def new_hotel(self):
        """Task pentru crearea unui nou hotel"""
        logging.info("Attempting to create new hotel")
        csrftoken = self.get_csrf_token("/newhotel/")
        if csrftoken:
            response = self.client.post("/newhotel/", {
                "name": "Hotel Test",
                "address": "123 Test St",
                "location": "Test City",
                "amenities": "wifi,pool,gym",
                "phone": "1234567890",
                "money": "200.00",
                "latitude": "45.0",
                "longitude": "-75.0",
                "csrfmiddlewaretoken": csrftoken
            }, headers={'X-CSRFToken': csrftoken})

            if response.status_code == 200:
                logging.info("New hotel created successfully")
            else:
                logging.error(f"Failed to create new hotel: {response.status_code} - {response.text}")
        else:
            logging.error("Failed to retrieve CSRF token for new hotel creation")

    @task
    def edit_hotel(self):
        """Task pentru editarea unui hotel existent"""
        logging.info("Attempting to edit a hotel")
        
        # Hotel list in order to find valid ID
        hotel_response = self.client.get("/landlord/")  # Endpoint for hotels
        if hotel_response.status_code == 200:
            hotels = hotel_response.json()
            if hotels:
                hotel_id = hotels[0]['id']  # First hotel ID
                csrftoken = self.get_csrf_token(f"/edit-hotel/{hotel_id}/")
                if csrftoken:
                    response = self.client.post(f"/edit-hotel/{hotel_id}/", {
                        "name": "Hotel Edited",
                        "address": "Edited Address",
                        "location": "Edited City",
                        "amenities": "wifi,pool,gym",
                        "phone": "1234567890",
                        "money": "150.00",
                        "latitude": "46.0",
                        "longitude": "-74.0",
                        "csrfmiddlewaretoken": csrftoken
                    }, headers={'X-CSRFToken': csrftoken})

                    if response.status_code == 200:
                        logging.info("Hotel edited successfully")
                    else:
                        logging.error(f"Failed to edit hotel: {response.status_code} - {response.text}")
                else:
                    logging.error("Failed to retrieve CSRF token for hotel editing")
            else:
                logging.error("No hotels available to edit")
        else:
            logging.error(f"Failed to retrieve hotels: {hotel_response.status_code} - {hotel_response.text}")


    @task
    def logout(self):
        """Task pentru logout"""
        logging.info("Attempting logout")
        response = self.client.get("/logout/")
        if response.status_code == 200:
            logging.info("Logout successful")
        else:
            logging.error(f"Failed to logout: {response.status_code} - {response.text}")

    def random_boolean(self):
        """Funcție pentru a genera true/false random"""
        from random import choice
        return choice([True, False])


class WebsiteUser(HttpUser):
    tasks = [UserBehavior]
    wait_time = between(1, 5)
    host = "http://127.0.0.1:8000"  
