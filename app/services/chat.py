from typing import Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from app.core.config import settings
from app.db.models import ChatLog
from app.schemas.chat import ChatInput
from sqlalchemy.orm import Session

from app.prompts.emotion_prompt import EMOTION_PROMPT
from app.prompts.atri_vietnamese_prompt import ATRI_VIETNAMESE_PROMPT
from app.prompts.atri_english_prompt import ATRI_ENGLISH_PROMPT

class ChatService:
    def __init__(self, db: Session):
        self.db = db
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            temperature=0.7,
            max_retries=2,
            google_api_key=settings.GOOGLE_API_KEY
        )
        
        # Initialize prompts
        self.emotion_prompt = ChatPromptTemplate.from_messages([
            ("system", EMOTION_PROMPT),
            ("human", "{text}")
        ])
        
        self.atri_prompt = ChatPromptTemplate.from_messages([
            ("system", ATRI_ENGLISH_PROMPT),
            ("human", "{input}")
        ])
        
        self.vietnamese_prompt = ChatPromptTemplate.from_messages([
            ("system", ATRI_VIETNAMESE_PROMPT),
            ("human", "{input}")
        ])
        
        # Initialize chains
        self.emotion_chain = self.emotion_prompt | self.llm
        self.atri_chain = self.atri_prompt | self.llm
        self.vietnamese_chain = self.vietnamese_prompt | self.llm

    async def _get_emotion(self, message: str) -> str:
        """Get emotion from user message."""
        emotion_response = self.emotion_chain.invoke(
            {"text": message}
        ).content.strip().lower()
        
        emotion = emotion_response.split()[-1].strip('.')
        return "neutral" if len(emotion) > 50 else emotion

    def _build_context(self, chat_input: ChatInput) -> str:
        """Build conversation context."""
        full_context = "\n".join([
            f"Human: {h}\nAtri: {a}" 
            for h, a in chat_input.conversation_history
        ])
        
        return (
            f"Previous conversation:\n{full_context}\n\nHuman: {chat_input.message}"
            if full_context else chat_input.message
        )

    async def _process_chat_common(
        self, 
        chat_input: ChatInput, 
        chain: Any
    ) -> Dict[str, str]:
        """Common chat processing logic."""
        try:
            emotion = await self._get_emotion(chat_input.message)
            current_input = self._build_context(chat_input)
            
            response = chain.invoke({
                "input": current_input,
                "emotion": emotion
            })

            chat_log = ChatLog(
                user_message=chat_input.message,
                bot_response=response.content,
                emotion=emotion
            )
            self.db.add(chat_log)
            self.db.commit()
            
            return {
                "response": response.content,
                "emotion": emotion
            }
            
        except Exception as e:
            self.db.rollback()
            raise e

    async def process_chat(self, chat_input: ChatInput) -> Dict[str, str]:
        """Process English chat."""
        return await self._process_chat_common(chat_input, self.atri_chain)
        
    async def process_vietnamese_chat(self, chat_input: ChatInput) -> Dict[str, str]:
        """Process Vietnamese chat."""
        return await self._process_chat_common(chat_input, self.vietnamese_chain)