# 🚀 Aforro Backend — Django + DRF + Redis + Celery + Docker

A production-style backend implementing product catalog, store inventory, transactional order processing, search with caching, autocomplete, and async task handling.

---

## ✨ Highlights

* **Transactional Orders** with `transaction.atomic()`
* **Race-condition safe stock updates** using `select_for_update()` + `F()`
* **Search API** with filters, sorting, pagination, and Redis caching
* **Autocomplete API** (fast, prefix-prioritized suggestions)
* **Async processing** via Celery (Redis broker)
* **Dockerized stack** (Django + PostgreSQL + Redis + Celery)

---

## 🧱 Tech Stack

* **Backend:** Django, Django REST Framework
* **Database:** PostgreSQL (Docker) / SQLite (local dev)
* **Cache & Broker:** Redis
* **Async Worker:** Celery
* **Containerization:** Docker, Docker Compose

---

## 📂 Project Structure

```
project/
│
├── products/
├── stores/
├── orders/
├── search/
├── core/                    # seed_data command
│
├── project/
│   ├── settings.py
│   ├── urls.py
│   ├── celery.py
│
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

## ⚙️ Setup

### 🔹 1) Clone

```bash
git clone <your-repo-url>
cd aforro-backend
```

---

## ▶️ Run Locally (SQLite)

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open: http://127.0.0.1:8000/admin/

---

## 🐳 Run with Docker (PostgreSQL + Redis + Celery)

```bash
docker-compose up --build
```

### 🔧 First-time initialization (inside container)

```bash
docker exec -it aforro-backend-web-1 bash

python manage.py migrate
python manage.py createsuperuser
python manage.py seed_data
```

Open: http://localhost:8000/admin/

---

## 📡 API Endpoints

### 🛒 Orders

* **POST** `/orders/`
  Create order (atomic, validates stock; CONFIRMED/REJECTED)

* **GET** `/stores/<store_id>/orders/`
  List orders with `order_id`, `status`, `created_at`, `total_items`

---

### 📦 Inventory

* **GET** `/stores/<store_id>/inventory/`
  Returns product title, price, category, quantity (sorted by title)

---

### 🔍 Product Search

* **GET** `/api/search/products/`

Query params:

* `q` (keyword across title/description/category)
* `category`
* `min_price`, `max_price`
* `store_id`
* `in_stock=true|false`
* `sort=price|-price|newest|relevance`
* `page`, `limit`

**Notes:**

* Cached via Redis (5 min TTL)
* When `store_id` is provided → includes per-store `quantity`

---

### ⚡ Autocomplete

* **GET** `/api/search/suggest/?q=xxx`
* Min 3 chars, max 10 results
* Prefix matches ranked before general matches

---

## 🌱 Seed Data

```bash
python manage.py seed_data
```

Generates:

* 10+ categories
* 1000+ products
* 20+ stores
* 300+ inventory items per store

---

## ⚡ Performance Decisions

* **Caching:** Search results cached in Redis to reduce DB load
* **Query Optimization:**

  * `select_related` / `prefetch_related` where needed
  * `annotate(Count(...))` for order item counts
* **Concurrency Safety:**

  * `select_for_update()` to lock inventory rows
  * `F()` expressions for atomic stock decrement

---

## 🔁 Asynchronous Tasks

* Order confirmation handled asynchronously via Celery
* Broker: Redis
* Worker runs as separate container

---

## 🧠 Design Notes

* Clean separation by apps: `products`, `stores`, `orders`, `search`
* Environment-aware settings:

  * Local → SQLite + localhost Redis
  * Docker → PostgreSQL (`db`) + Redis (`redis`)
* Idempotent order creation flow (rejects on insufficient stock without mutation)

---

## ⚠️ Common Gotchas

* After starting Docker, always run:

  ```bash
  python manage.py migrate
  ```
* If Celery can’t connect to Redis:

  * Ensure broker URL uses `redis://redis:6379/0` (service name, not localhost)

---

## 🎯 Conclusion

This project demonstrates:

* Robust REST API design
* Data modeling and consistency guarantees
* Query optimization and caching strategies
* Asynchronous processing with Celery
* Containerized deployment for reproducibility

---

## 👨‍💻 Author

**Muqhtadeer**
