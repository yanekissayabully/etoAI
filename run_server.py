import uvicorn
import os
from dotenv import load_dotenv

load_dotenv()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    
    print("🚀 Запускаю WABA AI Analyzer...")
    print(f"📡 Сервер: http://localhost:{port}")
    print(f"📚 Документация: http://localhost:{port}/docs")
    print("🛑 Для остановки нажми Ctrl+C")
    print("-" * 50)
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )