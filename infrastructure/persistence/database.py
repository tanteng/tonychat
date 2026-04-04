import os
import uuid
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from sqlalchemy import create_engine, Column, String, Integer, DateTime, Text
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import StaticPool

# 北京时区
BEIJING_TZ = timezone(timedelta(hours=8))

def now_beijing():
    """获取当前北京时间"""
    return datetime.now(BEIJING_TZ)

Base = declarative_base()


class Session(Base):
    __tablename__ = 'sessions'

    id = Column(String(36), primary_key=True)  # UUID
    title = Column(String(200), nullable=False, default='新会话')
    created_at = Column(DateTime, default=now_beijing)
    updated_at = Column(DateTime, default=now_beijing, onupdate=now_beijing)


class ConversationMessage(Base):
    __tablename__ = 'conversation_messages'

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(100), index=True, nullable=False)
    role = Column(String(20), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=now_beijing)


class Database:
    _instance = None

    def __init__(self):
        db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'chat.db')
        db_path = os.path.abspath(db_path)

        self.engine = create_engine(
            f'sqlite:///{db_path}',
            connect_args={'check_same_thread': False},
            poolclass=StaticPool
        )
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def add_message(self, session_id: str, role: str, content: str) -> ConversationMessage:
        """Add a message to the conversation history"""
        session = self.Session()
        try:
            msg = ConversationMessage(
                session_id=session_id,
                role=role,
                content=content
            )
            session.add(msg)
            session.commit()
            return msg
        finally:
            session.close()

    def get_conversation_history(self, session_id: str, limit: int = 20) -> List[ConversationMessage]:
        """Get conversation history for a session"""
        session = self.Session()
        try:
            messages = session.query(ConversationMessage)\
                .filter(ConversationMessage.session_id == session_id)\
                .order_by(ConversationMessage.created_at.asc())\
                .limit(limit)\
                .all()
            return messages
        finally:
            session.close()

    def clear_conversation_history(self, session_id: str) -> None:
        """Clear all messages for a session"""
        session = self.Session()
        try:
            session.query(ConversationMessage)\
                .filter(ConversationMessage.session_id == session_id)\
                .delete()
            session.commit()
        finally:
            session.close()

    def delete_messages_after(self, session_id: str, after_id: int) -> None:
        """Delete all messages after a specific message ID"""
        session = self.Session()
        try:
            session.query(ConversationMessage)\
                .filter(ConversationMessage.session_id == session_id)\
                .filter(ConversationMessage.id > after_id)\
                .delete()
            session.commit()
        finally:
            session.close()

    # Session methods
    def create_session(self) -> Session:
        """Create a new session with a generated UUID"""
        session = self.Session()
        try:
            new_session = Session(
                id=str(uuid.uuid4()),
                title='新会话'
            )
            session.add(new_session)
            session.commit()
            session.refresh(new_session)
            return new_session
        finally:
            session.close()

    def get_session(self, session_id: str) -> Optional[Session]:
        """Get a specific session by ID"""
        session = self.Session()
        try:
            return session.query(Session).filter(Session.id == session_id).first()
        finally:
            session.close()

    def get_all_sessions(self) -> List[Session]:
        """Get all sessions ordered by updated_at descending"""
        session = self.Session()
        try:
            return session.query(Session).order_by(Session.updated_at.desc()).all()
        finally:
            session.close()

    def update_session_title(self, session_id: str, title: str) -> None:
        """Update the title of a session"""
        session = self.Session()
        try:
            s = session.query(Session).filter(Session.id == session_id).first()
            if s:
                s.title = title
                s.updated_at = now_beijing()
                session.commit()
        finally:
            session.close()

    def delete_session(self, session_id: str) -> None:
        """Delete a session and all its associated messages"""
        session = self.Session()
        try:
            # Delete associated messages first
            session.query(ConversationMessage)\
                .filter(ConversationMessage.session_id == session_id)\
                .delete()
            # Delete the session
            session.query(Session)\
                .filter(Session.id == session_id)\
                .delete()
            session.commit()
        finally:
            session.close()

    def touch_session(self, session_id: str) -> None:
        """Update the updated_at timestamp of a session"""
        session = self.Session()
        try:
            s = session.query(Session).filter(Session.id == session_id).first()
            if s:
                s.updated_at = now_beijing()
                session.commit()
        finally:
            session.close()


# Global singleton
_db: Optional[Database] = None


def get_database() -> Database:
    global _db
    if _db is None:
        _db = Database.get_instance()
    return _db
