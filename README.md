# Eurovision Voting App

A simple Eurovision Song Contest 2025 voting application built with Flask, JSON storage, and vanilla JavaScript. Users can register, login, vote in two semi-finals, and a grand final. Administrators can manage finalists and orders.

## Features

* User registration and login with JWT authentication
* Two semi-final rounds and a grand final
* Score voting (0–12) and final selection
* Separate admin controls to add/remove artists to grand final and adjust performance order
* Real-time results aggregation
* Responsive and styled with CSS gradients

## Tech Stack

* Python 3.9+
* Flask
* Flask-JWT-Extended
* Flask-Migrate (optional if using database)
* JSON files for data storage (`artists.json`, `votes.json`, `grand_final.json`)
* Vanilla JavaScript
* HTML/CSS (Flexbox, gradients)

## Prerequisites

* Python 3.9+
* pip
* (Optional) virtual environment

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/yourusername/eurovision-voting-app.git
   cd eurovision-voting-app
   ```

2. (Optional) Create and activate a virtual environment:

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Linux/macOS
   venv\\Scripts\\activate  # Windows
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Initialize data files (if not present, JSON files are created automatically on first run):

   ```bash
   touch data/artists.json data/users.json data/votes.json data/grand_final.json
   ```

## Configuration

Set environment variables or create a `.env` file in the project root:

```dotenv
SECRET_KEY="your_flask_secret_key"
DATABASE_URL="sqlite:///eurovision.db"  # if using database
```

## Running the Application

```bash
python app.py
```

The app will run at `http://127.0.0.1:5000` by default.

## API Endpoints

* `POST /api/register` – Register a new user
* `POST /api/login` – Authenticate and retrieve JWT
* `GET /api/semi-finals/<n>` – Get artists for semi-final *n*
* `GET /api/grand-final` – Get artists in grand final
* `POST /api/vote` – Submit score/final selection
* `POST /api/grand-vote` – Submit grand final score/winner selection
* `GET /api/results` – View aggregated semi-final results
* `GET /api/results-final` – View aggregated grand final results
* `POST /api/admin/final/<id>` – Admin toggle grand final inclusion
* `PUT /api/admin/final/order/<id>` – Admin change final order

## File Structure

```
eurovision_app/
├── app.py                   # Flask application
├── data/
│   ├── artists.json        # List of all artists
│   ├── users.json          # Registered users
│   ├── votes.json          # User votes for semis
│   └── grand_final.json    # Artists in grand final
│   └── grand_votes.json    # User votes for grand final
├── static/
│   ├── css/style.css       # Stylesheet
│   └── js/main.js          # Frontend logic
└── templates/              # HTML templates
    ├── index.html
    ├── register.html
    ├── dashboard.html
    ├── semi_final.html
    ├── final_page.html
    ├── results_page.html
    └── grand_results_page.html
```

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## License

This project is licensed under the MIT License. Feel free to use and modify!
