import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend"

sys.path.append(str(BACKEND_ROOT))

from app.database import Base, SessionLocal, engine  # noqa: E402
from app.models import KnowledgeChunk  # noqa: E402
from app.rag.chunker import chunk_text  # noqa: E402
from app.rag.embeddings import embed_text  # noqa: E402


KB_DIR = PROJECT_ROOT / "kb"


def load_markdown_files() -> list[Path]:
    if not KB_DIR.exists():
        raise FileNotFoundError(f"Knowledge base directory not found: {KB_DIR}")

    files = sorted(KB_DIR.glob("*.md"))

    if not files:
        raise FileNotFoundError(f"No markdown files found in: {KB_DIR}")

    return files


def seed_knowledge_base(reset: bool = False) -> None:
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        if reset:
            deleted = db.query(KnowledgeChunk).delete()
            print(f"Deleted existing knowledge chunks: {deleted}")
            db.commit()

        markdown_files = load_markdown_files()

        total_chunks = 0

        for file_path in markdown_files:
            text = file_path.read_text(encoding="utf-8")
            chunks = chunk_text(text)

            print(f"\nDocument: {file_path.name}")
            print(f"Chunks  : {len(chunks)}")

            for chunk in chunks:
                embedding = embed_text(chunk)

                knowledge_chunk = KnowledgeChunk(
                    source_doc=file_path.name,
                    chunk_text=chunk,
                    embedding=embedding,
                )

                db.add(knowledge_chunk)
                total_chunks += 1

        db.commit()

        print("\n" + "=" * 80)
        print("Knowledge base seeding complete")
        print("=" * 80)
        print(f"Documents indexed : {len(markdown_files)}")
        print(f"Chunks created    : {total_chunks}")
        print("=" * 80)

    finally:
        db.close()


def parse_args():
    parser = argparse.ArgumentParser(
        description="Seed internal knowledge base markdown files into knowledge_chunks table."
    )

    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete existing knowledge chunks before seeding.",
    )

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    seed_knowledge_base(reset=args.reset)