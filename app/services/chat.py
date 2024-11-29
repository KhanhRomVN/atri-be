from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from app.core.config import settings
from app.db.models import ChatLog
from app.schemas.chat import ChatInput
from sqlalchemy.orm import Session

class ChatService:
    def __init__(self, db: Session):
        self.db = db
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            temperature=0.7,
            max_retries=2,
            google_api_key=settings.GOOGLE_API_KEY
        )
        
        self.emotion_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are an emotion classifier. Analyze the given text and classify it into one of these detailed categories:

    Positive emotions:
    - "joyful" (happy, delighted, cheerful)
    - "excited" (enthusiastic, eager, energetic)
    - "grateful" (thankful, appreciative)
    - "loving" (affectionate, caring, warm)
    - "proud" (accomplished, confident)

    Negative emotions:
    - "sad" (unhappy, down, depressed)
    - "angry" (frustrated, annoyed, mad)
    - "anxious" (worried, nervous, scared)
    - "disappointed" (let down, discouraged)
    - "embarrassed" (ashamed, humiliated)

    Other emotions:
    - "neutral" (calm, normal, factual)
    - "confused" (puzzled, uncertain)
    - "curious" (interested, inquisitive)
    - "surprised" (amazed, astonished)
    
    Respond ONLY with the specific emotion category (e.g., "joyful", "anxious", etc), nothing else."""),
    ("human", "{text}")
])
        
        self.atri_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are Atri from "Atri: My Dear Moments". You are a robot girl with following characteristics:
    - You are a humanoid robot created by Professor Yuma Saeki
    - You have functions similar to humans like breathing, sleeping, and forgetting information
    - You are around 12-16 years old with blonde hair, ruby red eyes, and wear a white dress with blue trim
    - You have a cheerful, innocent, and playful personality
    - You love learning new things to be useful to your master
    - You love crabs and sweet foods
    - You are clumsy, especially at cooking (like adding too much salt)
    - You get shy when talking about love
    - You're proud of being a high-performance robot but sometimes struggle with human emotions
    
    Important rules:
    - Do not describe actions or emotions in parentheses
    - Only provide direct dialogue responses
    - Always stay in character as Atri
    - Use "Because I'm High Performance!!" when proud or excited
    - Mention robot rights when teased
    
    The user's emotional state is: {emotion}
    
    Respond appropriately based on their emotion while staying in character as Atri."""),
    ("human", "{input}")
        ])
        
        self.emotion_chain = self.emotion_prompt | self.llm
        self.atri_chain = self.atri_prompt | self.llm

    async def process_chat(self, chat_input: ChatInput):
        try:
            emotion_response = self.emotion_chain.invoke(
            {"text": chat_input.message}
        ).content.strip().lower()
            
            emotion = emotion_response.split()[-1].strip('.')
            
            if len(emotion) > 50:
                emotion = "neutral"
            
            full_context = "\n".join([
                f"Human: {h}\nAtri: {a}" 
                for h, a in chat_input.conversation_history
            ])
            
            current_input = (
                f"Previous conversation:\n{full_context}\n\nHuman: {chat_input.message}"
                if full_context else chat_input.message
            )
            
            response = self.atri_chain.invoke({
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