# 🌱 Project Vision & Roadmap

This repository started as a minimal FastAPI + SQLite stack demonstrating a two-player Prisoner’s Dilemma. The long‑term goal is to grow it into a reusable Python module and a no‑code builder for online experiments.

## 1. Python Module

* Package the database helpers and game logic as an installable module.
* Provide a simple API to create sessions, manage players, and store decisions.
* Allow the database location to be configured via environment variables so it works on any host.

## 2. Visual Game Builder

* Develop a web UI where researchers design the flow of their game using drag‑and‑drop “boxes.”
* Each box represents a step in the sequence (information page, decision page, waiting page, etc.).
* Dynamic info boxes will be able to query the API and display state‑dependent content.
* When the design is finished the tool will automatically produce:
  * `app.py` – FastAPI endpoints tailored to the game.
  * `game_db.py` – database schema and helpers.
  * `Dockerfile` – for easy deployment to services like Hugging Face Spaces.

## 3. Qualtrics Integration

* Generate JavaScript snippets that call the API from within Qualtrics surveys.
* Examples include writing a player’s move, reading an opponent’s decision, or waiting until both players have advanced.
* This makes multiplayer experiments accessible to researchers comfortable with Qualtrics but not with Python coding.

## 4. Hosting & Deployment

* Support simple deployment to Hugging Face, Heroku, or any container host.
* Users will only need to upload the generated files and configure their API URL in the front end.

## 5. AI‑Assisted Helpers

* Use LLM APIs behind the scenes to suggest ready‑to‑use Qualtrics scripts.
* Provide templates for common economic games so new projects can start quickly.

---

This roadmap aims to democratize online experiments by removing the barrier of custom back‑end coding. Feedback and contributions are welcome!
