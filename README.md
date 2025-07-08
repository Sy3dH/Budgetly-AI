# Budgetly-AI
The repository includes the AI features of the Budgetly app.

## Project Setup with Docker Compose

This guide will help you set up and run the application using Docker Compose.

### Prerequisites

- Docker installed on your system
- Docker Compose installed on your system
- A Gemini API key from Google AI Studio

### Quick Start

#### Step 1: Environment Configuration

Create a `.env` file in the root directory of your project and add your Gemini API key:

```bash
GEMINI_API_KEY=your_gemini_api_key_here
```
In order to use the query API for talking to the database, provide the `MYSQL-HOST`, `MYSQL-DATABASE`, `MYSQL-USER` & `MYSQL-PASSWORD` in the `.env`.

**Important:** Replace `your_gemini_api_key_here` with your actual Gemini API key.

#### Step 2: Build and Run

Run the following command to build and start all services:

```bash
docker-compose up --build
```

This command will:
- Build the Docker images for both server and client
- Start all containers defined in your docker-compose.yml
- Set up the necessary networking between services

#### Step 3: Access the Application

Once the containers are running, you can access the Streamlit application by opening your web browser and navigating to:

```
http://localhost:8501
```

The Streamlit app will provide you with everything you need to run and interact with the application.

### Services

After running `docker-compose up --build`, the following services will be available:

- **Server**: Backend service handling API requests
- **Client**: Streamlit frontend application accessible at `localhost:8501`

### Stopping the Application

To stop all running containers, use:

```bash
docker-compose down
```

### Troubleshooting

- **Port conflicts**: If port 8501 is already in use, you can modify the port mapping in your docker-compose.yml file
- **API key issues**: Ensure your Gemini API key is valid and properly set in the `.env` file
- **Build errors**: Try running `docker-compose down` followed by `docker-compose up --build` to rebuild from scratch

### Getting a Gemini API Key

1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Create a new API key
4. Copy the key and paste it into your `.env` file

---

That's it! Your application should now be running and accessible through your web browser.
