import uvicorn
import os
import sys

if __name__ == "__main__":
    # Ensure backend directory is in python path
    backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend")
    sys.path.insert(0, backend_dir)

    print("🚀 옷깃(OatGit) 백엔드 서버를 시작합니다...")
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
