import subprocess
import sys

def fix_dependencies():
    """Исправляет зависимости"""
    print("🔧 Исправляю зависимости...")
    
    # Список правильных версий
    deps = [
        "fastapi==0.104.1",
        "uvicorn[standard]==0.24.0", 
        "openai==1.3.0",
        "python-dotenv==1.0.0",
        "requests==2.31.0",
        "aiohttp==3.9.1",
        "pydantic==2.5.0"
    ]
    
    # Обновляем pip
    print("📦 Обновляю pip...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
    
    # Устанавливаем зависимости
    for dep in deps:
        print(f"📦 Устанавливаю {dep}...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", dep])
            print(f"✅ {dep} установлен")
        except subprocess.CalledProcessError as e:
            print(f"⚠️  Ошибка установки {dep}: {e}")
    
    print("\n✅ Зависимости исправлены!")
    print("👉 Теперь запускай: python main.py")

if __name__ == "__main__":
    fix_dependencies()