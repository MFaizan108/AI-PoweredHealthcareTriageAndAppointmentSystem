# 15. AI Patient Assistant

Separate AI chatbot:

```
Patient:
"When is my appointment?"

AI:
"Your appointment with Dr. Ahmed is
tomorrow at 10:30 AM."
```

Lekin chatbot ko patient ke authorized system data tak hi access do.

Ye RAG-based assistant bhi ban sakta hai:

```
User
 ↓
Permission Check
 ↓
Retriever
 ↓
Patient's authorized records / hospital FAQs
 ↓
LLM
 ↓
Response
```
