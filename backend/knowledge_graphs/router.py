from fastapi import APIRouter, Depends, HTTPException
from typing import List
import sqlite3
from auth.service import get_current_user
from .models import User, KnowledgeGraph, KnowledgeGraphCreate
import os
from dotenv import load_dotenv
import uuid
import requests
import json

load_dotenv()
KNOWLEDGE_GRAPHS_DB_PATH = os.getenv("KNOWLEDGE_GRAPHS_DB_PATH")
CURRENT_API_PATH = os.getenv("API_PATH")
GRAPH_DATA_DIR = os.getenv("GRAPH_DATA_DIR")

router = APIRouter(prefix="/knowledge-graphs", tags=["knowledge_graphs"])

def get_db():
    conn = sqlite3.connect(KNOWLEDGE_GRAPHS_DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

from fastapi import BackgroundTasks

def trigger_pipeline(uuid: str, query: str):
    print("Sent pipeline trigger")
    requests.post(
        f"{CURRENT_API_PATH}/pipelines/generate-knowledge-graph",
        json={
            "uuid": uuid,
            "query": query
        }
    )

@router.post("/")
async def create_knowledge_graph(
    graph: KnowledgeGraphCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db)
):
    cursor = db.cursor()
    generated_uuid = str(uuid.uuid4())
    try:
        cursor.execute(
            """
            INSERT INTO knowledge_graphs (uuid, title, user_id)
            VALUES (?, ?, ?)
            """,
            (generated_uuid, graph.title, graph.user_id)
        )
        db.commit()
        
        cursor.execute(
            """
            SELECT uuid, title, user_id
            FROM knowledge_graphs 
            WHERE uuid = ?
            """,
            (generated_uuid,)
        )
        result = cursor.fetchone()
        
        # Trigger the pipeline as a background task
        background_tasks.add_task(trigger_pipeline, generated_uuid, graph.title)

        return dict(result)

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=List[KnowledgeGraph])
async def list_knowledge_graphs(
    current_user: User = Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db)
):
    cursor = db.cursor()
    cursor.execute(
        """
        SELECT uuid, title, user_id
        FROM knowledge_graphs 
        WHERE user_id = ?
        """,
        (current_user.id,)
    )
    return [dict(row) for row in cursor.fetchall()]

@router.get("/{uuid}")
async def get_knowledge_graph(
    uuid: str,
    current_user: User = Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db)
):
    cursor = db.cursor()
    cursor.execute(
        """
        SELECT uuid, title, user_id
        FROM knowledge_graphs 
        WHERE uuid = ? AND user_id = ?
        """,
        (uuid, current_user.id)
    )
    graph = cursor.fetchone()

    if not graph:
        raise HTTPException(status_code=404, detail="Knowledge graph not found")

    with open(os.path.join(GRAPH_DATA_DIR, uuid, "articles.json"), "r") as f:
        graph_data = json.load(f)

    nodes = []
    links = []
    possibilities = [("[["+st+"]]", st) for st in graph_data.keys() if st != "GRAPH_NAME"]
    for article_name in graph_data.keys():
        if article_name != "GRAPH_NAME":
            node = {
                "id": article_name,
                "name": article_name,
                "content": graph_data[article_name]["article"],
                "chunks": graph_data[article_name]["chunks"]
            }
            nodes.append(node)

            for possibility in possibilities:
                if possibility[0] in graph_data[article_name]["article"]:
                    if {"source": possibility[1], "target": article_name} not in links:
                        if possibility[1] != article_name:
                            
                            link = {
                                "source": article_name,
                                "target": possibility[1]
                            }
                            links.append(link)
    
    out = {
        "name": graph_data["GRAPH_NAME"],
        "nodes": nodes,
        "links": links
    }
    
    return out
    
@router.get("/status/{uuid}")
async def get_knowledge_graph_status(
    uuid: str,
    current_user: User = Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db)
):
    cursor = db.cursor()
    cursor.execute(
        """
        SELECT uuid, title, status
        FROM knowledge_graphs 
        WHERE uuid = ? AND user_id = ?
        """,
        (uuid, current_user.id)
    )
    graph = cursor.fetchone()
    
    if not graph:
        raise HTTPException(status_code=404, detail="Knowledge graph not found")
    
    return dict(graph)

@router.put("/status/{uuid}/{status}")
async def update_knowledge_graph_status(
    uuid: str,
    status: str,
    db: sqlite3.Connection = Depends(get_db)
):
    cursor = db.cursor()
    cursor.execute(
        """
        UPDATE knowledge_graphs
        SET status = ?
        WHERE uuid = ?
        """,
        (status, uuid)
    )
    db.commit()

@router.put("/title/{uuid}/{title}")
async def update_knowledge_graph_title(
    uuid: str,
    title: str,
    db: sqlite3.Connection = Depends(get_db)
):
    cursor = db.cursor()
    cursor.execute(
        """
        UPDATE knowledge_graphs
        SET title = ?
        WHERE uuid = ?
        """,
        (title, uuid)
    )
    db.commit()

@router.delete("/{uuid}")
async def delete_knowledge_graph(
    uuid: str,
    current_user: User = Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db)
):
    cursor = db.cursor()
    cursor.execute(
        """
        DELETE FROM knowledge_graphs 
        WHERE uuid = ? AND user_id = ?
        """,
        (uuid, current_user.id)
    )
    db.commit()
    
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Knowledge graph not found")
    
    return {"message": "Knowledge graph deleted"}
