import uvicorn

if __name__ == "__main__":
    print("Starting EduQuestion AI API server on http://localhost:8000 ...")
    print("Swagger Documentation: http://localhost:8000/docs")
    print("Interactive Playground: http://localhost:8000/demo")
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
