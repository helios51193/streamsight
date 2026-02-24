# 📊 Stream Sight

A realtime event ingestion and analytics system built with:

-   **Django (ASGI + Channels)**
-   **Redis (rolling minute aggregation)**
-   **WebSockets**
-   **Alpine.js**
-   **Tailwind CSS + DaisyUI**
-   **Dockerized deployment**

------------------------------------------------------------------------

## 📸 Screenshots

![Document List](screenshots/Screenshot_1.png)

![Document List](screenshots/Screenshot_2.png)

------------------------------------------------------------------------

## 🚀 Features

-   Realtime event ingestion API
-   Redis-backed rolling minute aggregation
-   Per-client dynamic time window
-   Server-side percentile (P95) calculation
-   WebSocket push updates (no polling)
-   Automatic reconnection handling
-   Persistent dashboard preferences
-   Dockerized deployment
-   Static file serving via WhiteNoise

------------------------------------------------------------------------

## 🧠 Architecture Overview

This system separates:

-   **Write Path** (Event ingestion)
-   **Aggregation Layer** (Redis buckets)
-   **Transport Layer** (WebSockets)
-   **Presentation Layer** (Alpine.js UI)

------------------------------------------------------------------------

## 🏗 High-Level Architecture

                ┌─────────────────────────┐
                │      Client (Browser)   │
                │  Alpine + Tailwind UI   │
                └─────────────┬───────────┘
                              │ WebSocket
                              ▼
                   ┌──────────────────────┐
                   │  Django ASGI Server  │
                   │  (Channels + Daphne) │
                   └─────────────┬────────┘
                                 │
                ┌────────────────┼────────────────┐
                │                │                │
                ▼                ▼                ▼
        Event Ingest API   Redis Aggregation   Database
            (POST)         (Minute Buckets)    (Persistence)

------------------------------------------------------------------------

## 🔁 Event Flow

1.  Client sends POST request to `/api/ingest/`
2.  Server saves event to DB
3.  Server updates Redis minute bucket
4.  Server broadcasts raw event via WebSocket
5.  Server aggregates last N buckets
6.  Server pushes metrics snapshot to client

------------------------------------------------------------------------

## 🐳 Running With Docker

### 1️⃣ Build Containers

    docker-compose build

### 2️⃣ Start Services

    docker-compose up

### 3️⃣ Open Application

Visit:

    http://localhost:8000

------------------------------------------------------------------------

## 📦 Redis Bucket Design

Each minute is stored as:

    metrics:{YYYYMMDDHHMM}

Example:

    metrics:202603181205

Stored fields:

-   total
-   success
-   error
-   duration_sum

Durations stored separately in:

    metrics:{bucket}:durations

Buckets auto-expire after 1 hour.

------------------------------------------------------------------------

## 📈 Metrics Computed

-   Total Events
-   Success Count
-   Error Count
-   Success Rate
-   Error Rate
-   Average Duration
-   P95 Duration
-   Events Per Minute

------------------------------------------------------------------------

## 🧩 Future Improvements

-   Redis sorted sets for percentile optimization
-   Server-side event-type filtering
-   Alert threshold system
-   Horizontal scaling
-   Nginx reverse proxy + HTTPS

------------------------------------------------------------------------

## 📌 License

This project is for educational and portfolio purposes.
