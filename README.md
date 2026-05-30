# 🌸 SafePath — Fix Our City Together
[🔗 Click here to view the live interactive map application](https://safepath-tx4t.onrender.com)

SafePath is a community-driven web platform where users can report city issues, view safety scores, and send emergency SOS alerts. It also rewards users with coins for contributing useful reports.

---

## 🚀 Features

- 👤 User registration & login system
- 📝 Report civic issues (potholes, garbage, etc.)
- 🆘 Emergency SOS alert system
- 🗺️ Interactive map using Leaflet.js
- 🔥 Heatmap of city issues
- 🏙️ City safety score calculator
- 🪙 Gamified coin reward system
- 🏆 Leaderboard for top contributors
- 🌙 Dark / Light theme support

---

## 🛠️ Tech Stack

### Frontend
- HTML
- CSS (Custom theming + animations)
- JavaScript (Vanilla JS)
- Leaflet.js (Maps API)

### Backend
- Python
- FastAPI
- SQLAlchemy (Database ORM)
- SQLite (Database)

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/register` | Create new user |
| GET | `/user/{username}` | Get user details |
| POST | `/report` | Submit civic issue |
| POST | `/sos` | Send emergency alert |
| GET | `/heatmap` | Get map data |
| GET | `/safe-zones` | Get safe zones |
| GET | `/city-score/{city}` | Get safety score |
| GET | `/leaderboard` | Top users |
| GET | `/reports` | Recent reports |

---
