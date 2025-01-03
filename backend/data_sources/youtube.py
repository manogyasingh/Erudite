from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
import requests
from datetime import datetime, timedelta
import concurrent.futures
from youtube_transcript_api import YouTubeTranscriptApi
from utils.text_chunking import TextChunker, ChunkingStrategy, RAGDocument
from utils.timing import timing_decorator

router = APIRouter()

# Load environment variables
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

class YouTubeSearchQuery(BaseModel):
    keywords: List[str]
    max_results: int = 10
    chunk_size: int = 3000
    chunk_overlap: int = 200
    chunking_strategy: ChunkingStrategy = ChunkingStrategy.RECURSIVE
    language: Optional[str] = None
    days_back: Optional[int] = 7

# @timing_decorator("Searching YouTube Videos")
def search_videos(query: str, max_results: int, language: Optional[str] = None, days_back: int = 7) -> List[dict]:
    """Search for YouTube videos using YouTube Data API."""
    try:
        url = "https://www.googleapis.com/youtube/v3/search"
        
        # Calculate date for filtering
        published_after = None
        if days_back:
            published_after = (datetime.utcnow() - timedelta(days=days_back)).isoformat() + "Z"
        
        params = {
            "part": "snippet",
            "q": query,
            "key": YOUTUBE_API_KEY,
            "maxResults": max_results,
            "type": "video",
            "relevanceLanguage": language,
            "publishedAfter": published_after
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        # print(response.json())
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)

        return response.json().get("items", [])
    except Exception as e:
        print(f"Error in YouTube search: {str(e)}")
        return []

# @timing_decorator("Getting Video Details")
def get_video_details(video_ids: List[str]) -> List[dict]:
    """Get detailed information about YouTube videos."""
    try:
        url = "https://www.googleapis.com/youtube/v3/videos"
        params = {
            "part": "snippet,statistics,contentDetails",
            "key": YOUTUBE_API_KEY,
            "id": ",".join(video_ids)
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        return response.json().get("items", [])
    except Exception as e:
        print(f"Error getting video details: {str(e)}")
        return []

# @timing_decorator("Getting Video Transcript")
def get_video_transcript(video_id: str, language: Optional[str] = None) -> List[dict]:
    """Get transcript for a YouTube video."""
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        
        # Try to get transcript in specified language, fallback to auto-generated
        try:
            if language:
                transcript = transcript_list.find_transcript(["en"])
            else:
                transcript = transcript_list.find_manually_created_transcript()
        except:
            transcript = transcript_list.find_generated_transcript(["en"])
            
        return transcript.fetch()
    except Exception as e:
        print(f"Error getting transcript for video {video_id}: {str(e)}")
        return []

# @timing_decorator("Processing Single Video")
def process_video(video: dict, chunker: TextChunker, language: Optional[str] = None) -> List[RAGDocument]:
    """Process a single YouTube video into RAG documents."""
    try:
        video_id = video["id"]["videoId"]
        
        # Get video details
        details = get_video_details([video_id])
        if not details:
            return []
            
        detail = details[0]
        
        # Get transcript
        transcript = get_video_transcript(video_id, language)
        if not transcript:
            return []
            
        # Create base metadata
        metadata = {
            "source": "youtube",
            "video_id": video_id,
            "title": detail["snippet"]["title"],
            "channel_title": detail["snippet"]["channelTitle"],
            "published_at": detail["snippet"]["publishedAt"],
            "view_count": detail["statistics"].get("viewCount"),
            "like_count": detail["statistics"].get("likeCount"),
            "comment_count": detail["statistics"].get("commentCount"),
            "duration": detail["contentDetails"]["duration"],
            "url": f"https://www.youtube.com/watch?v={video_id}",
            "source_database": "youtube_data_api"
        }
        
        # Create documents
        documents = []
        
        # Create summary document
        summary_content = f"Title: {detail['snippet']['title']}\n\n"
        if detail["snippet"].get("description"):
            summary_content += f"Description: {detail['snippet']['description']}"
            
        summary_metadata = {
            **metadata,
            "chunk_type": "summary",
            "is_full_text": False
        }
        
        documents.append(RAGDocument(
            content=summary_content.strip(),
            metadata=summary_metadata
        ))
        
        # Process transcript into chunks
        transcript_text = ""
        current_timestamp = 0
        
        for entry in transcript:
            timestamp = entry["start"]
            text = entry["text"]
            
            # Add timestamp markers for chunking
            if timestamp - current_timestamp > 30:  # New segment if >30s gap
                transcript_text += f"\n[{timestamp:.2f}s]\n"
                current_timestamp = timestamp
                
            transcript_text += f"{text} "
            
        # Create content chunks
        content_metadata = {
            **metadata,
            "chunk_type": "transcript",
            "is_full_text": True
        }
        content_docs = chunker.create_documents(transcript_text.strip(), content_metadata)
        documents.extend(content_docs)
        
        return documents
        
    except Exception as e:
        print(f"Error processing video {video.get('id', {}).get('videoId')}: {str(e)}")
        return []

@router.post("/search")
@timing_decorator("YouTube Search Endpoint")
def search_videos_endpoint(query: YouTubeSearchQuery):
    """Search YouTube videos and return RAG-ready documents."""
    try:
        # Initialize text chunker
        chunker = TextChunker(
            chunk_size=query.chunk_size,
            chunk_overlap=query.chunk_overlap,
            strategy=query.chunking_strategy
        )
        
        # Search videos
        search_query = " ".join(query.keywords)
        videos = search_videos(
            search_query,
            query.max_results,
            query.language,
            query.days_back
        )
        
        # Process videos into RAG documents in parallel
        all_documents = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(videos)) as executor:
            future_to_video = {
                executor.submit(process_video, video, chunker, query.language): video
                for video in videos
            }
            
            for future in concurrent.futures.as_completed(future_to_video):
                try:
                    documents = future.result()
                    all_documents.extend(documents)
                except Exception as e:
                    print(f"Error processing video into documents: {str(e)}")
        
        return {
            "documents": [doc.dict() for doc in all_documents],
            "total_chunks": len(all_documents),
            "total_results": len(videos)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
