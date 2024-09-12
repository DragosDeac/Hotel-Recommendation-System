Hello Reader! :)

Thank you for checking out this project. This web application offers personalized hotel recommendations based on user preferences, and it's built using Django, SQLite, HTML, CSS, and JavaScript. Below, I’ll walk you through how to set up everything and get it running.

Getting Started
Prerequisites
Make sure you have the following installed:
Python 3.x
pip (Python package installer)
Virtualenv - VENV (optional but recommended)
Locust - great & easy to use for load testing.

1. Set Up Your Virtual Environment
To keep your environment clean, we must create a virtual environment.

    1. Open your terminal and navigate to the project folder: **cd /path-to-your-project-folder**

    2. Create and activate VENV: **python3 -m venv venv**


2. Please install all the project dependancies using **pip install xxxxxx**
3. Generate and add your GoogleMaps API_KEY in newhotel.html - I am not sharing mine.
4. Set up your database: **python manage.py migrate**
5. Run the server and have fun!: **python manage.py runserver**
   You now may access http://127.0.0.1:8000/
6. Optionally, check out the Locust testing - It runs amazing, I ran it for over 2 hours, getting 0 Failed http requests at 50 constant users.
   In order to do that, you may run: **locust -f locustfile.py**
   You may now acess http://127.0.0.1:8089

That’s it! You’ve now set up the project and can run both the Django server and Locust for testing. If you run into any issues or have questions, feel free to reach out.

Happy coding and testing! 😊
