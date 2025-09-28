#!/usr/bin/env python3
"""
문서 빌드 스크립트

이 스크립트는 Sphinx 문서를 빌드하고 검증합니다.
"""

import os
import subprocess
import sys
from pathlib import Path


def main():
    """메인 함수"""
    # 프로젝트 루트 디렉토리로 이동
    project_root = Path(__file__).parent.parent
    docs_dir = project_root / "docs"

    print("📚 Asset Allocation 문서 빌드 시작...")

    # docs 디렉토리로 이동
    os.chdir(docs_dir)

    try:
        # Sphinx 문서 빌드
        print("🔨 Sphinx 문서 빌드 중...")
        subprocess.run(
            ["uv", "run", "sphinx-build", "-b", "html", "source", "build"],
            check=True,
            capture_output=True,
            text=True,
        )

        print("✅ 문서 빌드 완료!")
        print(f"📁 빌드된 문서 위치: {docs_dir / 'build' / 'index.html'}")

        # 빌드 결과 확인
        index_file = docs_dir / "build" / "index.html"
        if index_file.exists():
            print(f"📖 문서를 보려면: open {index_file}")
        else:
            print("❌ 빌드된 문서를 찾을 수 없습니다.")
            return 1

    except subprocess.CalledProcessError as e:
        print(f"❌ 문서 빌드 실패: {e}")
        print(f"에러 출력: {e.stderr}")
        return 1
    except FileNotFoundError:
        print("❌ uv 명령어를 찾을 수 없습니다. uv가 설치되어 있는지 확인하세요.")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
