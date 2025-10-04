from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.dependencies import get_current_user
from src.db.models import User
from src.db.session import get_db
from src.schemas.chat import (
    ConversationCreate,
    ConversationList,
    ConversationRead,
    ConversationUpdate,
    MessageCreate,
    MessageList,
    MessageRead,
)
from src.services import chat as chat_service

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/conversations", response_model=ConversationRead, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    conversation_data: ConversationCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ConversationRead:
    """Create a new conversation."""
    conversation = await chat_service.create_conversation(db, conversation_data, current_user.id)
    return ConversationRead.model_validate(conversation)


@router.get("/conversations", response_model=ConversationList)
async def list_conversations(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ConversationList:
    """List all conversations for the current user."""
    conversations = await chat_service.get_user_conversations(db, current_user.id)
    return ConversationList(
        conversations=[ConversationRead.model_validate(c) for c in conversations],
        total=len(conversations),
    )


@router.get("/conversations/{conversation_id}", response_model=ConversationRead)
async def get_conversation(
    conversation_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ConversationRead:
    """Get a conversation by ID."""
    conversation = await chat_service.get_conversation_by_id(db, conversation_id, current_user.id)
    return ConversationRead.model_validate(conversation)


@router.patch("/conversations/{conversation_id}", response_model=ConversationRead)
async def update_conversation(
    conversation_id: int,
    conversation_data: ConversationUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ConversationRead:
    """Update a conversation."""
    conversation = await chat_service.update_conversation(
        db, conversation_id, conversation_data, current_user.id
    )
    return ConversationRead.model_validate(conversation)


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> None:
    """Delete a conversation."""
    await chat_service.delete_conversation(db, conversation_id, current_user.id)


@router.get("/conversations/{conversation_id}/messages", response_model=MessageList)
async def list_messages(
    conversation_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> MessageList:
    """List all messages in a conversation."""
    messages = await chat_service.get_conversation_messages(db, conversation_id, current_user.id)
    return MessageList(
        messages=[MessageRead.model_validate(m) for m in messages],
        total=len(messages),
    )


@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=MessageRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_message(
    conversation_id: int,
    message_data: MessageCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> MessageRead:
    """Create a new message in a conversation.

    Note: In Phase 3, this only stores the message without AI response.
    AI integration will be added in Phase 4.
    """
    message = await chat_service.create_message(db, conversation_id, message_data, current_user.id)
    return MessageRead.model_validate(message)
