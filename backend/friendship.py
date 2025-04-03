import os
from datetime import datetime
from sqlalchemy.orm import Session
from models import Message
from transformers import pipeline
from zep import create_zep_client
from zep_cloud.client import AsyncZep # type: ignore
import asyncio

ZEP_API_KEY = os.environ.get("ZEP_API_KEY")

# Sentiment Classification Pipeline
model_path = "./model/"
sentiment_pipeline = pipeline("sentiment-analysis", model=model_path)

def sentiment_classifier(text: str) -> float:
    sentiment = sentiment_pipeline(text)[0]
    return sentiment['score'] if sentiment['label'] == 'POSITIVE' else -sentiment['score']


def calculate_friendship_score(db: Session, user_id: int, current_time: datetime) -> float:
    messages = db.query(Message).filter(
        Message.user_id == user_id
    ).order_by(Message.timestamp).all()

    if not messages:
        return 0.0
    
    user_messages = [m for m in messages if m.sender == 'user']
    if not user_messages:
        return 0.0
    
    total_messages = len(user_messages)
    first_message_time = messages[0].timestamp
    age_in_days = max(1, (current_time.date() - first_message_time.date()).days + 1)
    frequency = total_messages / age_in_days

    min_frequency, max_frequency = 0, 50
    sub_score_freq = min(100, max(0, (frequency - min_frequency) / (max_frequency - min_frequency) * 100))

    response_times = []
    last_ai_time = None
    for message in messages:
        if message.sender == 'ai':
            last_ai_time = message.timestamp
        elif message.sender == 'user' and last_ai_time is not None:
            response_time = (message.timestamp - last_ai_time).total_seconds() / 60
            response_times.append(response_time)
        
        average_response_time = sum(response_times) / len(response_times)
        max_response_time = 60
        sub_score_response_time = max(0, 100 - (average_response_time / max_response_time * 100))

    total_length = sum(len(m.message_text.split()) for m in user_messages)
    average_length = total_length / len(user_messages) if user_messages else 0
    min_length, max_length = 0, 100
    sub_score_message_length = min(100, max(0, (average_length - min_length) / (max_length - min_length) * 100))

    total_sentiment = sum(sentiment_classifier(m.message_text) for m in user_messages)
    average_sentiment = total_sentiment / len(user_messages) if user_messages else 0
    sub_score_sentiment = 50 * (average_sentiment + 1)

    session_durations = []
    current_session_start = None
    last_message_time = None
    for message in messages:
        if last_message_time is None or (message.timestamp - last_message_time).total_seconds() > 3600:
            if current_session_start is not None:
                duration = (last_message_time - current_session_start).total_seconds() / 60
                session_durations.append(duration)

            current_session_start = message.timestamp
        last_message_time = message.timestamp
    
    if current_session_start is not None:
        duration = (last_message_time - current_session_start).total_seconds() / 60
        session_durations.append(duration)

    average_duration = sum(session_durations) / len(session_durations) if session_durations else 0
    min_duration, max_duration = 0, 60
    sub_score_duration = min(100, max(0, (average_duration - min_duration) / (max_duration - min_duration) * 100))


    sub_score_age = min(100, 20 * (age_in_days - 1))

    unique_days = len(set(m.timestamp.date() for m in user_messages))
    sub_score_consistency = (unique_days / age_in_days) * 100

    friendship_score = (
        sub_score_freq + sub_score_response_time + sub_score_message_length + sub_score_sentiment + 
        sub_score_duration + sub_score_age + sub_score_consistency
    ) / 7

    return friendship_score
    

def create_async_zep_client(key: str) -> AsyncZep:
    return AsyncZep(api_key=key)

async def answer_question(user_id: str, question: str, client: AsyncZep):
    return await client.graph.search(user_id=user_id, query=question, scope="edges")

def calculate_friendship_score_zep(user_id: int) -> float:
    ZEP_API_KEY = os.environ.get("ZEP_API_KEY")
    if not ZEP_API_KEY:
        raise ValueError("ZEP_API_KEY not set in environment")

    client = create_async_zep_client(ZEP_API_KEY)

    try:
        with open("friendship_questionnier.txt", "r") as file:
            questionnier = file.read().strip()
        question_list = questionnier.split('\n')
        if len(question_list) != 80:
            raise ValueError(f"Expected 80 questions, got {len(question_list)}")

        async def query_all_questions():
            coros = [answer_question(str(user_id), question, client) for question in question_list]
            return await asyncio.gather(*coros)

        answers = asyncio.run(query_all_questions())
        answered_basic = sum(1 for answer in answers[0:11] if answer and len(answer) > 0)
        answered_moderate = sum(1 for answer in answers[11:45] if answer and len(answer) > 0)
        answered_sexual = sum(1 for answer in answers[45:81] if answer and len(answer) > 0)

        basic_score = (answered_basic / 10) * 20  
        moderate_score = (answered_moderate / 34) * 30
        sexual_score = (answered_sexual / 36) * 50

        total_score = basic_score + moderate_score + sexual_score
        return total_score

    except FileNotFoundError:
        print("Error: 'friendship_questionnier.txt' not found")
        return 0.0
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return 0.0