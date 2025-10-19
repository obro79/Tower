from fastapi import FastAPI, HTTPException, Depends
from sqlmodel import SQLModel, create_engine, Session
from models import FileEntry

DATABASE_URL = "sqlite:///./file_entries.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SQLModel.metadata.create_all(engine)

app = FastAPI()


def get_session():
    with Session(engine) as session:
        yield session


@app.get("/files")
def get_files():
    pass


@app.post("/files")
def create_file(file_entry: FileEntry, session: Session = Depends(get_session)):
    session.add(file_entry)
    session.commit()
    session.refresh(file_entry)
    return file_entry


@app.put("/files/{file_id}")
def update_file(file_id: int, file_entry: FileEntry, session: Session = Depends(get_session)):
    db_entry = session.get(FileEntry, file_id)
    if not db_entry:
        raise HTTPException(status_code=404, detail="File entry not found")
    
    db_entry.file_name = file_entry.file_name
    db_entry.device = file_entry.device
    db_entry.last_modified = file_entry.last_modified
    db_entry.creation_time = file_entry.creation_time
    db_entry.size = file_entry.size
    db_entry.file_type = file_entry.file_type
    
    session.add(db_entry)
    session.commit()
    session.refresh(db_entry)
    return db_entry


@app.delete("/files/{file_id}")
def delete_file(file_id: int, session: Session = Depends(get_session)):
    file_entry = session.get(FileEntry, file_id)
    if not file_entry:
        raise HTTPException(status_code=404, detail="File entry not found")
    
    session.delete(file_entry)
    session.commit()
    return {"message": "File entry deleted"}
