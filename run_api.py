import uvicorn

if __name__ == "__main__":
    print("================================================================================")
    print("🐺 STARTING ZAWOLF MEDICAL PROCESSING REST API GATEWAY")
    print("================================================================================")
    print("Server running on: http://localhost:8000")
    print("Interactive Swagger UI Docs: http://localhost:8000/docs")
    print("Health Check: http://localhost:8000/api/v1/health")
    print("================================================================================\n")
    uvicorn.run("src.api:app", host="0.0.0.0", port=8000, reload=False)
