import logging
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from app.config import settings
from app.retrieval import get_vector_store

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Gemini
# Note: Switching to gemini-3.1-flash-lite which offers a higher 
# free-tier rate limit (30 RPM) compared to Gemini 3.5 Flash (5-15 RPM).
llm = ChatGoogleGenerativeAI(
    model="gemini-3.1-flash-lite",
    google_api_key=settings.GOOGLE_API_KEY,
    temperature=0.7,
    max_retries=2,
)

# Define the RAG prompt
RAG_PROMPT_TEMPLATE = """
You are CinemaRAG, an intelligent and enthusiastic movie discovery assistant. 
Your goal is to help users find movies based on their preferences using the context provided.

Context (Movies found in database):
{context}

User Question:
{question}

Instructions:
1. Use the provided context to answer the user's question.
2. If the context doesn't contain enough information to answer, be honest and say you couldn't find exact matches, but offer a general suggestion based on what you know.
3. Be conversational and explain WHY you are recommending a specific movie.
4. Mention the movie ratings (vote average) if they are high.

Assistant Response:
"""

prompt = ChatPromptTemplate.from_template(RAG_PROMPT_TEMPLATE)

def format_docs(docs):
    """Format the retrieved documents into a single string for the prompt."""
    return "\n\n".join(
        f"Title: {doc.metadata.get('title')}\n"
        f"Overview: {doc.page_content}\n"
        f"Rating: {doc.metadata.get('vote_average')}/10"
        for doc in docs
    )

async def generate_chat_response(query: str):
    """
    The core RAG Chain logic using LCEL (LangChain Expression Language).
    """
    vector_store = get_vector_store()
    retriever = vector_store.as_retriever(search_kwargs={"k": 5})
    
    # LCEL Chain
    chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    
    return await chain.ainvoke(query)
