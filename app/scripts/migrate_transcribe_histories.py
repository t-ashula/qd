#!/usr/bin/env python3
"""
Script to migrate existing data to the new transcribe_histories structure.

This script:
1. Creates transcribe_histories records for existing episodes
2. Updates episode_segments to link to the new transcribe_histories
3. Updates Qdrant payloads to include transcribe_history_id and model_name
"""

import os
import sys
from typing import Dict, List

# Add the parent directory to sys.path to import app modules
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.models.models import Episode, EpisodeSegment, TranscribeHistory
from app.vectorstore.qdrant import qdrant_manager

# Default model name for existing episodes
DEFAULT_MODEL_NAME = "kotoba-tech/kotoba-whisper-v2.2"


def migrate_transcribe_histories():
    """
    Migrate existing episodes to use transcribe_histories
    """
    # Create database session
    db = SessionLocal()

    try:
        # Get all episodes
        episodes = db.query(Episode).all()
        print(f"Found {len(episodes)} episodes to migrate")

        # Process each episode
        for episode in episodes:
            print(f"Processing episode {episode.id} ({episode.name})")

            # Create transcribe history record
            history = TranscribeHistory(
                episode_id=episode.id,
                model_name=DEFAULT_MODEL_NAME,
                created_at=episode.created_at,
            )
            db.add(history)
            db.flush()  # Get ID without committing

            # Update episode segments
            segments_count = (
                db.query(EpisodeSegment)
                .filter(
                    EpisodeSegment.episode_id == episode.id,
                    EpisodeSegment.transcribe_history_id.is_(None),
                )
                .update({"transcribe_history_id": history.id})
            )

            print(
                f"  Updated {segments_count} segments with transcribe_history_id={history.id}"
            )

            # Update Qdrant payloads
            update_qdrant_payloads(episode.id, history.id, DEFAULT_MODEL_NAME)

        # Commit all changes
        db.commit()
        print("Migration completed successfully")

    except Exception as e:
        db.rollback()
        print(f"Error during migration: {e}")
        raise
    finally:
        db.close()


def update_qdrant_payloads(episode_id: str, history_id: int, model_name: str):
    """
    Update Qdrant payloads for an episode

    Args:
        episode_id: Episode ID
        history_id: Transcribe history ID
        model_name: Model name
    """
    try:
        # Update E5 collection
        update_collection_payloads("episodes_e5", episode_id, history_id, model_name)

        # Update V2 collection
        update_collection_payloads("episodes_v2", episode_id, history_id, model_name)

        print(f"  Updated Qdrant payloads for episode {episode_id}")
    except Exception as e:
        print(f"  Error updating Qdrant payloads for episode {episode_id}: {e}")


def update_collection_payloads(
    collection_name: str, episode_id: str, history_id: int, model_name: str
):
    """
    Update payloads in a specific Qdrant collection

    Args:
        collection_name: Collection name
        episode_id: Episode ID
        history_id: Transcribe history ID
        model_name: Model name
    """
    # Get points for this episode
    from qdrant_client.http.models import FieldCondition, Filter, MatchValue

    filter_condition = Filter(
        must=[FieldCondition(key="episode_id", match=MatchValue(value=episode_id))]
    )

    # Use pagination to get all points
    offset = None
    total_updated = 0

    while True:
        # Search for points with this episode_id
        search_result = qdrant_manager.client.scroll(
            collection_name=collection_name,
            scroll_filter=filter_condition,
            limit=100,  # Process in batches of 100
            with_payload=True,
            with_vectors=False,
            offset=offset,
        )

        points = search_result[0]  # First element is the list of points
        offset = search_result[1]  # Second element is the offset for pagination

        if not points:
            break  # No more points to process

        # Collect point IDs and prepare payload update
        point_ids = []

        for point in points:
            point_ids.append(point.id)

        # Update all points in this batch with a single operation
        if point_ids:
            payload_update = {
                "transcribe_history_id": history_id,
                "model_name": model_name,
            }

            qdrant_manager.client.set_payload(
                collection_name=collection_name,
                payload=payload_update,
                points=point_ids,
            )

            total_updated += len(point_ids)

        # If no offset returned, we've processed all points
        if offset is None:
            break

    print(f"    Updated {total_updated} points in {collection_name} collection")


if __name__ == "__main__":
    print("Starting migration of transcribe histories...")
    migrate_transcribe_histories()
    print("Migration completed.")
